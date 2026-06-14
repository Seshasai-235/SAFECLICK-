"""
Dataset Collection Script for SafeClick Evaluation

This script helps collect phishing and legitimate URLs from various sources
and formats them into a test dataset.
"""

import json
import requests
import csv
from typing import List, Dict
from datetime import datetime

# Configuration
PHISHTANK_URL = "http://data.phishtank.com/data/online-valid.json"
OPENPHISH_URL = "https://openphish.com/feed.txt"
OUTPUT_FILE = "test_dataset.json"

# Legitimate URLs (manually curated)
LEGITIMATE_URLS = [
    # Search Engines
    "https://www.google.com",
    "https://www.bing.com",
    "https://www.yahoo.com",
    "https://duckduckgo.com",
    
    # Tech Companies
    "https://www.microsoft.com",
    "https://www.apple.com",
    "https://www.amazon.com",
    "https://www.meta.com",
    "https://www.netflix.com",
    "https://www.adobe.com",
    
    # AI Services
    "https://chat.openai.com",
    "https://www.anthropic.com",
    "https://claude.ai",
    "https://gemini.google.com",
    
    # Social Media
    "https://www.facebook.com",
    "https://www.instagram.com",
    "https://www.twitter.com",
    "https://www.linkedin.com",
    "https://www.reddit.com",
    "https://www.tiktok.com",
    
    # E-commerce
    "https://www.ebay.com",
    "https://www.walmart.com",
    "https://www.target.com",
    "https://www.bestbuy.com",
    "https://www.etsy.com",
    
    # Financial
    "https://www.paypal.com",
    "https://www.stripe.com",
    "https://www.chase.com",
    "https://www.bankofamerica.com",
    "https://www.wellsfargo.com",
    
    # Streaming
    "https://www.youtube.com",
    "https://www.spotify.com",
    "https://www.hulu.com",
    "https://www.disneyplus.com",
    "https://www.twitch.tv",
    
    # Development
    "https://github.com",
    "https://gitlab.com",
    "https://stackoverflow.com",
    "https://www.npmjs.com",
    "https://pypi.org",
    
    # Cloud Services
    "https://aws.amazon.com",
    "https://cloud.google.com",
    "https://azure.microsoft.com",
    "https://www.cloudflare.com",
    "https://www.digitalocean.com",
    
    # Education
    "https://www.wikipedia.org",
    "https://www.coursera.org",
    "https://www.udemy.com",
    "https://www.khanacademy.org",
    "https://www.edx.org",
    
    # News
    "https://www.nytimes.com",
    "https://www.bbc.com",
    "https://www.cnn.com",
    "https://www.reuters.com",
    "https://www.theguardian.com",
    
    # Government
    "https://www.usa.gov",
    "https://www.irs.gov",
    "https://www.cdc.gov",
    "https://www.nasa.gov",
    
    # Email Services
    "https://mail.google.com",
    "https://outlook.live.com",
    "https://mail.yahoo.com",
    
    # Productivity
    "https://www.notion.so",
    "https://www.slack.com",
    "https://www.zoom.us",
    "https://www.dropbox.com",
    "https://www.trello.com",
]


def fetch_phishtank_urls(limit: int = 500) -> List[Dict]:
    """Fetch phishing URLs from PhishTank"""
    print("Fetching phishing URLs from PhishTank...")
    
    try:
        response = requests.get(PHISHTANK_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        phishing_urls = []
        for idx, entry in enumerate(data[:limit], 1):
            phishing_urls.append({
                "id": idx,
                "url": entry["url"],
                "ground_truth": "Phishing",
                "category": "Phishing",
                "source": "PhishTank",
                "verified": entry.get("verified", "yes"),
                "target": entry.get("target", "Unknown")
            })
        
        print(f"✅ Fetched {len(phishing_urls)} phishing URLs from PhishTank")
        return phishing_urls
    
    except Exception as e:
        print(f"❌ Error fetching PhishTank data: {str(e)}")
        return []


def fetch_openphish_urls(limit: int = 500) -> List[Dict]:
    """Fetch phishing URLs from OpenPhish"""
    print("Fetching phishing URLs from OpenPhish...")
    
    try:
        response = requests.get(OPENPHISH_URL, timeout=30)
        response.raise_for_status()
        urls = response.text.strip().split('\n')
        
        phishing_urls = []
        for idx, url in enumerate(urls[:limit], 1):
            if url.strip():
                phishing_urls.append({
                    "id": idx,
                    "url": url.strip(),
                    "ground_truth": "Phishing",
                    "category": "Phishing",
                    "source": "OpenPhish"
                })
        
        print(f"✅ Fetched {len(phishing_urls)} phishing URLs from OpenPhish")
        return phishing_urls
    
    except Exception as e:
        print(f"❌ Error fetching OpenPhish data: {str(e)}")
        return []


def get_legitimate_urls() -> List[Dict]:
    """Get legitimate URLs from curated list"""
    print("Loading legitimate URLs...")
    
    legitimate_urls = []
    for idx, url in enumerate(LEGITIMATE_URLS, 1):
        legitimate_urls.append({
            "id": idx,
            "url": url,
            "ground_truth": "Legitimate",
            "category": categorize_url(url),
            "source": "Curated List"
        })
    
    print(f"✅ Loaded {len(legitimate_urls)} legitimate URLs")
    return legitimate_urls


def categorize_url(url: str) -> str:
    """Categorize URL based on domain"""
    url_lower = url.lower()
    
    if any(x in url_lower for x in ['google', 'bing', 'yahoo', 'duckduckgo']):
        return "Search Engine"
    elif any(x in url_lower for x in ['facebook', 'instagram', 'twitter', 'linkedin', 'reddit']):
        return "Social Media"
    elif any(x in url_lower for x in ['amazon', 'ebay', 'walmart', 'target']):
        return "E-commerce"
    elif any(x in url_lower for x in ['paypal', 'stripe', 'chase', 'bank']):
        return "Financial"
    elif any(x in url_lower for x in ['netflix', 'youtube', 'spotify', 'hulu']):
        return "Streaming"
    elif any(x in url_lower for x in ['github', 'gitlab', 'stackoverflow']):
        return "Development"
    elif any(x in url_lower for x in ['microsoft', 'apple', 'adobe']):
        return "Technology"
    elif any(x in url_lower for x in ['openai', 'anthropic', 'claude']):
        return "AI Services"
    elif any(x in url_lower for x in ['.gov']):
        return "Government"
    else:
        return "Other"


def create_balanced_dataset(phishing_urls: List[Dict], legitimate_urls: List[Dict], 
                           phishing_count: int = 500, legitimate_count: int = 500) -> Dict:
    """Create a balanced dataset with equal phishing and legitimate samples"""
    
    # Take specified number of samples
    phishing_sample = phishing_urls[:phishing_count]
    legitimate_sample = legitimate_urls[:legitimate_count]
    
    # Combine and re-index
    all_samples = []
    for idx, sample in enumerate(phishing_sample + legitimate_sample, 1):
        sample['id'] = idx
        all_samples.append(sample)
    
    dataset = {
        "description": "SafeClick Test Dataset for Model Evaluation",
        "created_at": datetime.now().isoformat(),
        "total_samples": len(all_samples),
        "phishing_samples": len(phishing_sample),
        "legitimate_samples": len(legitimate_sample),
        "sources": {
            "phishing": ["PhishTank", "OpenPhish"],
            "legitimate": ["Curated List"]
        },
        "samples": all_samples
    }
    
    return dataset


def save_dataset(dataset: Dict, filename: str):
    """Save dataset to JSON file"""
    with open(filename, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\n✅ Dataset saved to: {filename}")
    print(f"   Total samples: {dataset['total_samples']}")
    print(f"   Phishing: {dataset['phishing_samples']}")
    print(f"   Legitimate: {dataset['legitimate_samples']}")


def print_dataset_summary(dataset: Dict):
    """Print dataset summary"""
    print("\n" + "="*60)
    print("DATASET SUMMARY")
    print("="*60)
    print(f"Total Samples: {dataset['total_samples']}")
    print(f"Phishing Samples: {dataset['phishing_samples']}")
    print(f"Legitimate Samples: {dataset['legitimate_samples']}")
    print(f"Balance: {(dataset['phishing_samples'] / dataset['total_samples'] * 100):.1f}% phishing")
    print("="*60)
    
    # Category breakdown
    categories = {}
    for sample in dataset['samples']:
        cat = sample.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory Breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    print("="*60)


def main():
    """Main function to collect and prepare dataset"""
    print("="*60)
    print("SafeClick Dataset Collection")
    print("="*60)
    
    # Fetch phishing URLs
    phishing_urls = []
    
    # Try PhishTank first
    phishtank_urls = fetch_phishtank_urls(limit=300)
    phishing_urls.extend(phishtank_urls)
    
    # Try OpenPhish if needed
    if len(phishing_urls) < 500:
        openphish_urls = fetch_openphish_urls(limit=500 - len(phishing_urls))
        phishing_urls.extend(openphish_urls)
    
    # Get legitimate URLs
    legitimate_urls = get_legitimate_urls()
    
    # Check if we have enough samples
    if len(phishing_urls) < 100:
        print("\n⚠️  Warning: Not enough phishing URLs collected!")
        print("   Please check your internet connection or try again later.")
        return
    
    if len(legitimate_urls) < 100:
        print("\n⚠️  Warning: Not enough legitimate URLs!")
        print("   Please add more URLs to the LEGITIMATE_URLS list.")
        return
    
    # Create balanced dataset
    dataset = create_balanced_dataset(
        phishing_urls, 
        legitimate_urls,
        phishing_count=min(500, len(phishing_urls)),
        legitimate_count=min(500, len(legitimate_urls))
    )
    
    # Print summary
    print_dataset_summary(dataset)
    
    # Save dataset
    save_dataset(dataset, OUTPUT_FILE)
    
    print("\n" + "="*60)
    print("Dataset collection complete!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Review the dataset in '{OUTPUT_FILE}'")
    print(f"2. Update API endpoint in 'evaluate_model.py'")
    print(f"3. Run: python evaluate_model.py")


if __name__ == "__main__":
    main()
