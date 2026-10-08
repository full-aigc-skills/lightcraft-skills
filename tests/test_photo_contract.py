"""照片流程与实际解码契约；合成图片不是原生验收。"""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    path=ROOT/'runtime'/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def png(path,width=3,height=2):
    def chunk(name,data):
        return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data))
    data=b''.join(b'\x00'+bytes([100,110,120])*width for _ in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))


class PhotoContract(unittest.TestCase):
    def test_actual_decoding_and_wrong_size(self):
        artifacts=load('artifacts')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/'image.png';png(path)
            fact=artifacts.verify(path,root,{'width':3,'height':2,'bitDepth':8,'format':'png'})
            self.assertEqual(fact['technicalStatus'],'PASS')
            self.assertEqual(artifacts.verify(path,root,{'width':9})['technicalStatus'],'FAIL')
            self.assertEqual(artifacts.verify(path,root,{'bitDepth':16,'colorSpace':'unavailable-profile'})['technicalStatus'],'FAIL')
            with self.assertRaisesRegex(ValueError,'outside_root'):artifacts.verify(path,root/'other')
            path.write_bytes(b'not an image')
            with self.assertRaises(ValueError):artifacts.verify(path,root)

    def test_unrelated_settings_stay_unchanged_and_controls_are_bounded(self):
        path=ROOT/'runtime/photo_workflows.py'
        self.assertTrue(path.exists(),'missing workflow contract')
        workflows=load('photo_workflows')
        baseline={'light':{'exposure':0.0},'crop':{'x':.2},'masks':[{'id':1}]}
        proposed=workflows.apply_local_changes(baseline,{'light.exposure':.5},[{'id':'light.exposure','min':-5,'max':5}])
        self.assertEqual(proposed['crop'],baseline['crop'])
        self.assertEqual(proposed['masks'],baseline['masks'])
        self.assertEqual(baseline['light']['exposure'],0.0)
        with self.assertRaises(ValueError):workflows.apply_local_changes(baseline,{'light.exposure':9},[{'id':'light.exposure','min':-5,'max':5}])

    def test_partial_import_keeps_duplicate_and_failed_identity(self):
        path=ROOT/'runtime/photo_workflows.py'
        self.assertTrue(path.exists(),'missing workflow contract')
        result=load('photo_workflows').import_summary({'imported':[1],'duplicates':[{'id':2,'path':'known'}],'failed':[['bad','decode failed']]},[{'id':1,'path':'new'},{'id':2,'path':'known'}])
        self.assertEqual(result['status'],'PARTIAL')
        self.assertEqual(result['photos'][1]['id'],2)
        self.assertEqual(result['failed'][0][0],'bad')

    def test_import_uses_native_existing_id_and_inspected_source(self):
        result=load('photo_workflows').import_summary(
            {'imported':[1],'duplicates':[{'path':'same.nef','existing':2,'reason':'content'}],'failed':[]},
            [{'id':1,'source':{'type':'file','path':'new.nef'}},{'id':2,'source':{'type':'file','path':'original.nef'}}])
        self.assertEqual([p['id'] for p in result['photos']],[1,2])
        self.assertEqual(result['photos'][1]['path'],'original.nef')
        self.assertEqual(result['unresolvedIds'],[])

    def test_duplicate_without_existing_identity_is_not_fully_reported(self):
        result=load('photo_workflows').import_summary(
            {'imported':[],'duplicates':[{'path':'same.nef','existing':None,'reason':'content'}],'failed':[]},[])
        self.assertEqual(result['status'],'IDENTITY_UNCONFIRMED')
        self.assertEqual(len(result['unresolvedDuplicates']),1)


if __name__=='__main__':unittest.main()
