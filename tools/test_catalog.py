"""Offline end-to-end tests; no third-party code or network required."""
import base64
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import collect_sources as c

class CatalogTests(unittest.TestCase):
    def test_parser(self):
        c.self_test()
        self.assertEqual(list(c.candidates('# What is this repository?')),[])

    def test_collection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); out=root/'expansion'; out.mkdir(); (root/'tools').mkdir()
            original='# Original\n- What is attention?\n'
            (root/'README.md').write_text(original)
            (root/'tools/catalog-template.html').write_text('<script type="application/json">__DATA__</script>')
            (out/'seeds.json').write_text(json.dumps([{'repo':'test/bank'},{'repo':'test/no-license'}]))
            (out/'curated.json').write_text(json.dumps([{'id':'p','topics':['agents'],'companies':['Example'],'sources':['https://example.org/docs'],'questions':['如何设计一个可以安全重试的智能体？']}]))
            archive=io.BytesIO()
            text=b'# What is attention?\n## Why test rollback?\n- Answer: Do not index this.\n'
            with tarfile.open(fileobj=archive,mode='w:gz') as tar:
                info=tarfile.TarInfo('snapshot/openai.md'); info.size=len(text);tar.addfile(info,io.BytesIO(text))
            def api(path):
                if '/commits/' in path:return {'sha':'a'*40}
                if '/license?' in path:
                    if 'no-license' in path: raise HTTPError('https://api.github.com',404,'not found',{},None)
                    return {'license':{'spdx_id':'MIT'},'content':base64.b64encode(('MIT License\n'+'permission notice '*30).encode()).decode()}
                return {'default_branch':'main','private':False}
            with patch.object(c,'ROOT',root), patch.object(c,'OUT',out), patch.object(c,'api',api), patch.object(c,'fetch',return_value=archive.getvalue()), patch.object(c.subprocess,'check_output',return_value=original.encode()):
                c.collect()
                first=json.loads((out/'questions.json').read_text())
                c.collect()
                second=json.loads((out/'questions.json').read_text())
            self.assertEqual(len(first),3)
            self.assertEqual([r['id'] for r in first],[r['id'] for r in second])
            self.assertIn('OpenAI',first[0]['companies'])
            self.assertTrue(first[0]['source_url'].endswith('#L2'))
            self.assertIn('additional_sources',first[0])
            self.assertTrue((root/'README.md').read_text().endswith(original))
            self.assertEqual((root/'README.md').read_text().count('<!-- AI-INTERVIEW-EXPANSION -->'),1)
            sources=json.loads((out/'sources.json').read_text())
            self.assertEqual(sources[1]['status'],'link_only_license_not_found')
            self.assertTrue((out/'licenses/test--bank.txt').exists())

if __name__=='__main__':unittest.main()
