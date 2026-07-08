"""TDD Tests - archwngs.py optimized version"""

import pytest, sys, os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))
from archwngs import search_files, fuzzy_search_files, open_in_explorer, open_app, SYSTEM_PROMPT, HAS_LEV, C_GRAY

class TestSearch:
    def test_search_returns_tuple(self):
        with patch('archwngs.os.walk') as w, patch('archwngs.os.path.isdir') as i:
            i.return_value = True; w.return_value = [('/h',[],['f.txt'])]
            r = search_files('f', '/h')
            assert isinstance(r, tuple) and len(r) == 2

    def test_search_shows_progress(self):
        with patch('archwngs.os.walk') as w, patch('archwngs.os.path.isdir') as i, patch('archwngs.p') as p:
            i.return_value = True; w.return_value = []
            search_files('x', '/h')
            assert any('Scanning' in str(c) for c in p.call_args_list)

class TestFuzzy:
    def test_fuzzy_returns_error_if_no_lev(self):
        if HAS_LEV: pytest.skip("Levenshtein installed")
        r, _ = fuzzy_search_files('test', '/h')
        assert 'ERROR' in r

class TestExplorer:
    def test_empty_path_error(self): assert 'ERROR' in open_in_explorer('')
    def test_invalid_path_error(self):
        with patch('os.path.isdir', return_value=False): assert 'ERROR' in open_in_explorer('/x')
    def test_valid_path_success(self):
        with patch('os.path.isdir', return_value=True), patch('platform.system', return_value='Windows'), patch('os.startfile') as s:
            r = open_in_explorer('/h'); assert 'SUCCESS' in r; s.assert_called_once()

class TestOpenApp:
    def test_nonexistent_error(self):
        with patch('archwngs.find_app', return_value=None):
            r, _ = open_app('fake123'); assert 'ERROR' in r and 'PATH' in r

class TestIdentity:
    def test_knows_dafa(self): assert 'Dafa' in SYSTEM_PROMPT
    def test_color_defined(self): assert '\033[90m' in C_GRAY

if __name__ == '__main__': pytest.main([__file__, '-v', '--tb=short'])
