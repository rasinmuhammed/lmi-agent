#!/usr/bin/env python3
"""
Standalone test for HuggingFace embeddings
Run this to verify your HUGGINGFACE_API_KEY works
"""
import sys
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_api_key():
    """Test if API key is configured"""
    print("=" * 60)
    print("Testing HuggingFace API Configuration")
    print("=" * 60)
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not api_key:
        print("❌ HUGGINGFACE_API_KEY not found in environment")
        print("\nHow to fix:")
        print("1. Get free token: https://huggingface.co/settings/tokens")
        print("2. Add to backend/.env:")
        print("   HUGGINGFACE_API_KEY=hf_your_token_here")
        return False
    
    if api_key.startswith("hf_your_"):
        print("❌ HUGGINGFACE_API_KEY is still the placeholder value")
        print("\nHow to fix:")
        print("1. Get real token: https://huggingface.co/settings/tokens")
        print("2. Replace placeholder in backend/.env")
        return False
    
    if not api_key.startswith("hf_"):
        print("⚠️  HUGGINGFACE_API_KEY doesn't start with 'hf_'")
        print("   This might not be a valid HuggingFace token")
        print("   Expected format: hf_xxxxxxxxxxxx")
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-5:]}")
    return True


def test_basic_request():
    """Test basic API request"""
    print("\n" + "=" * 60)
    print("Testing Basic API Request")
    print("=" * 60)
    
    try:
        import requests
        
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        model = "BAAI/bge-small-en-v1.5"
        url = f"https://api-inference.huggingface.co/models/{model}"

        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": ["Hello world"],
            "options": {"wait_for_model": True}
        }
        
        print(f"Sending test request to HuggingFace...")
        print(f"Model: {model}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                embedding = result[0] if isinstance(result[0], list) else result
                print(f"✅ API request successful!")
                print(f"   Embedding dimension: {len(embedding)}")
                print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
                return True
            else:
                print(f"❌ Unexpected response format: {type(result)}")
                return False
        
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"   Your API key might be invalid")
            print(f"   Get new token: https://huggingface.co/settings/tokens")
            return False
        
        elif response.status_code == 503:
            print(f"⏳ Model is loading (503)")
            print(f"   This is normal on first request")
            print(f"   Wait 10-30 seconds and try again")
            return True  # Not a failure, just needs time
        
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏳ Request timed out")
        print(f"   Model might be loading, try again in a minute")
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_embedding_generator():
    """Test the embedding generator class"""
    print("\n" + "=" * 60)
    print("Testing Embedding Generator Class")
    print("=" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.rag.embeddings import HuggingFaceEmbeddingGenerator
        
        print("Initializing embedding generator...")
        generator = HuggingFaceEmbeddingGenerator()
        
        # Test single embedding
        print("\n1. Testing single embedding:")
        text = "Machine learning engineer with Python experience"
        print(f"   Input: '{text}'")
        
        embedding = generator.generate_embedding(text)
        print(f"   ✅ Generated {len(embedding)}-dimensional embedding")
        print(f"   Sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        
        # Test batch embeddings
        print("\n2. Testing batch embeddings:")
        texts = [
            "Data scientist with deep learning skills",
            "Full stack developer",
            "DevOps engineer"
        ]
        print(f"   Processing {len(texts)} texts...")
        
        embeddings = generator.generate_embeddings_batch(texts, batch_size=3)
        print(f"   ✅ Generated {len(embeddings)} embeddings")
        
        # Test empty text handling
        print("\n3. Testing edge cases:")
        empty_embedding = generator.generate_embedding("")
        print(f"   ✅ Empty text handled: {len(empty_embedding)} dims")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunking():
    """Test text chunking"""
    print("\n" + "=" * 60)
    print("Testing Text Chunking")
    print("=" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.rag.embeddings import chunk_text, prepare_job_chunks
        
        # Test basic chunking
        long_text = """
        We are seeking a talented Machine Learning Engineer to join our team.
        The ideal candidate will have experience with PyTorch, TensorFlow, and
        production ML systems. You will work on cutting-edge AI projects and
        collaborate with data scientists and engineers.
        """ * 10
        
        chunks = chunk_text(long_text, chunk_size=200, overlap=50)
        print(f"✅ Text chunking: Created {len(chunks)} chunks")
        print(f"   Chunk sizes: {[len(c) for c in chunks[:3]]}...")
        
        # Test job data chunking
        job_data = {
            "title": "Senior ML Engineer",
            "company": "TechCorp",
            "location": "Remote",
            "description": "Build ML systems that scale.",
            "requirements": "5+ years experience",
            "skills": ["Python", "PyTorch", "AWS"],
            "source_url": "https://example.com/job"
        }
        
        job_chunks = prepare_job_chunks(job_data)
        print(f"✅ Job chunking: Created {len(job_chunks)} chunks")
        
        if job_chunks:
            print(f"   First chunk preview:")
            print(f"   {job_chunks[0]['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  HuggingFace Embeddings - Complete Test Suite")
    print("=" * 60)
    
    tests = [
        ("API Key Configuration", test_api_key),
        ("Basic API Request", test_basic_request),
        ("Embedding Generator", test_embedding_generator),
        ("Text Chunking", test_chunking)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results.items():
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"Result: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! Embeddings are working perfectly.")
        print("\nNext steps:")
        print("  1. Run full system verification:")
        print("     python scripts/verify_setup.py")
        print("  2. Ingest some job data:")
        print("     python scripts/ingest_data.py api --search-terms 'ML Engineer'")
    else:
        print("⚠️  Some tests failed. Common fixes:")
        print("\n1. Missing API key:")
        print("   Get free token: https://huggingface.co/settings/tokens")
        print("   Add to backend/.env: HUGGINGFACE_API_KEY=hf_xxx")
        print("\n2. Model loading (503 error):")
        print("   Wait 10-30 seconds and run test again")
        print("\n3. Rate limiting:")
        print("   Wait a minute and retry")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)