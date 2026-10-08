"""实际图像解码与版本化产物事实；不将配置当成文件证据。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(path, output_root, expected=None):
    """解码实际文件；Pillow 或 macOS sips，缺少解码器时拒绝通过。"""
    raw_path = Path(path).expanduser().absolute()
    if raw_path.is_symlink(): raise ValueError('artifact_symlink')
    path = raw_path.resolve()
    root = Path(output_root).expanduser().resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('artifact_outside_root_or_symlink')
    expected = expected or {}
    before = sha(path)
    color = None; icc = None; bits = None
    try:
        from PIL import Image, ImageCms
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size; fmt = image.format.lower()
            bits = (16 if image.mode.startswith('I;16') else 32 if image.mode in ('I','F') else 8)
            if image.format == 'TIFF':
                tags = image.tag_v2.get(258)
                if tags: bits = max(tags) if isinstance(tags, tuple) else tags
            profile = image.info.get('icc_profile')
            if profile:
                import io
                icc = hashlib.sha256(profile).hexdigest()
                color = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(profile))).strip()
            elif image.info.get('srgb') is not None:
                color = 'sRGB'
        decoder = 'Pillow'
    except ImportError:
        if not shutil.which('sips'):
            raise ValueError('image_decoder_required: Pillow or macOS sips')
        # sips 转码完整像素，临时产物不作为用户交付；仅读取原图。
        with tempfile.TemporaryDirectory(prefix='lightcraft-decode-') as temporary:
            decoded = Path(temporary) / 'decoded.png'
            conversion = subprocess.run(['sips', '-s', 'format', 'png', str(path), '--out', str(decoded)], capture_output=True, text=True, timeout=60)
            if conversion.returncode or not decoded.is_file():
                raise ValueError('artifact_decode_failed: ' + conversion.stderr[-1000:])
            with decoded.open('rb') as stream: header = stream.read(33)
            if header[:8] != b'\x89PNG\r\n\x1a\n':
                raise ValueError('decoder_output_invalid')
            width, height = struct.unpack('>II', header[16:24])
        properties = subprocess.run(['sips', '-g', 'format', '-g', 'bitsPerSample', '-g', 'profile', str(path)], capture_output=True, text=True, check=True, timeout=20)
        props = {}
        for line in properties.stdout.splitlines()[1:]:
            if ': ' in line:
                key, value = line.strip().split(': ', 1); props[key] = value
        fmt = props.get('format', '').lower()
        if props.get('bitsPerSample', '').isdigit(): bits = int(props['bitsPerSample'])
        color = props.get('profile')
        if color in ('<nil>', 'none'): color = None
        decoder = 'macOS sips'
    except (OSError, ValueError) as error:
        raise ValueError('artifact_decode_failed: ' + str(error)) from error
    if sha(path) != before:
        raise ValueError('artifact_changed_during_verification')
    with path.open('rb') as stream: header=stream.read(25)
    if header[:8] == b'\x89PNG\r\n\x1a\n': bits=header[24]
    aliases = {'jpg': 'jpeg', 'tif': 'tiff'}
    fmt = aliases.get(fmt, fmt)
    actual = {'format': fmt, 'width': width, 'height': height, 'bitDepth': bits}
    errors = {}
    for key in ('format', 'width', 'height', 'bitDepth'):
        wanted = expected.get(key)
        if key == 'format' and wanted: wanted = aliases.get(wanted.lower(), wanted.lower())
        if wanted is not None and actual[key] != wanted: errors[key] = {'expected': wanted, 'actual': actual[key]}
    if expected.get('colorSpace'):
        # 有明确元数据才能确认；RGB 通道类别不能证明 sRGB/P3。
        wanted = expected['colorSpace'].lower().replace(' ', '')
        if not color or wanted not in color.lower().replace(' ', ''):
            errors['colorSpace'] = {'expected': expected['colorSpace'], 'actual': color}
    if expected.get('iccSha256') is not None and icc != expected['iccSha256']:
        errors['iccSha256'] = {'expected': expected['iccSha256'], 'actual': icc}
    result = {'schemaVersion': 1, 'path': str(path), 'bytes': path.stat().st_size, 'sha256': before,
              **actual, 'colorProfile': color, 'iccSha256': icc, 'decoder': decoder,
              'decodable': True, 'technicalStatus': 'FAIL' if errors else 'PASS',
              'differences': errors, 'visualAcceptance': 'NOT_RUN'}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.path, args.output_root, json.loads(args.expected.read_text()) if args.expected else {})
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(0 if result['technicalStatus'] == 'PASS' else 1)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'technicalStatus': 'FAIL', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)
