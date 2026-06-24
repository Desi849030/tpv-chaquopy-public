from unittest.mock import MagicMock,patch
import pytest
class MockSC:
    def __init__(self):self.table=MagicMock();self.auth=MagicMock()
    def table(self,n):return self.table
def mock_supabase():
    with patch("supabase_sync.SupabaseClient") as m:yield m.return_value
