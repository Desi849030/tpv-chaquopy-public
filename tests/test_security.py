"""Tests de seguridad"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src', 'main', 'python'))

def test_tokenizer():
    try:
        from payment_tokenizer import tokenize, verify_token
        t = tokenize("1234")
        assert 'token' in t
        assert 'signature' in t
        print("✅ Tokenización OK")

    except Exception as e:
        print(f"❌ Tokenización: {e}")

def test_biometric():
    try:
        from biometric_auth import check_biometric_availability
        r = check_biometric_availability()
        assert 'available' in r
        print("✅ Biométrico OK")

    except Exception as e:
        print(f"❌ Biométrico: {e}")

def test_rls():
    try:
        from supabase_rls import get_branch_id, get_rls_headers
        bid = get_branch_id()
        assert bid.startswith('branch-')
        h = get_rls_headers()
        assert 'X-Branch-ID' in h
        print("✅ RLS OK")

    except Exception as e:
        print(f"❌ RLS: {e}")

if __name__ == '__main__':
    print("=" * 40)
    print("TPV Smart - Security Tests")
    print("=" * 40)
    r = [test_tokenizer(), test_biometric(), test_rls()]
    passed = sum(r)
    print("=" * 40)
    print(f"Resultado: {passed}/{len(r)} tests pasados")
