"""
Demo Evaluation - Small Scale Test
Tests 10 URLs to demonstrate the evaluation process
"""

import json
from datetime import datetime

# Demo dataset - 10 URLs (5 legitimate + 5 phishing examples)
DEMO_DATASET = {
    "description": "Demo dataset for SafeClick evaluation",
    "total_samples": 10,
    "phishing_samples": 5,
    "legitimate_samples": 5,
    "samples": [
        # Legitimate URLs
        {
            "id": 1,
            "url": "https://www.google.com",
            "ground_truth": "Legitimate",
            "category": "Search Engine"
        },
        {
            "id": 2,
            "url": "https://www.microsoft.com",
            "ground_truth": "Legitimate",
            "category": "Technology"
        },
        {
            "id": 3,
            "url": "https://www.amazon.com",
            "ground_truth": "Legitimate",
            "category": "E-commerce"
        },
        {
            "id": 4,
            "url": "https://github.com",
            "ground_truth": "Legitimate",
            "category": "Development"
        },
        {
            "id": 5,
            "url": "https://www.netflix.com",
            "ground_truth": "Legitimate",
            "category": "Streaming"
        },
        # Phishing examples (these are EXAMPLES - not real phishing sites)
        # In real evaluation, you'd use actual phishing URLs from PhishTank
        {
            "id": 6,
            "url": "http://paypal-verify-account.suspicious-domain.com",
            "ground_truth": "Phishing",
            "category": "Financial Phishing",
            "note": "Example - not a real URL"
        },
        {
            "id": 7,
            "url": "http://amazon-security-alert.fake-site.com",
            "ground_truth": "Phishing",
            "category": "E-commerce Phishing",
            "note": "Example - not a real URL"
        },
        {
            "id": 8,
            "url": "http://microsoft-account-suspended.phishing-example.com",
            "ground_truth": "Phishing",
            "category": "Tech Phishing",
            "note": "Example - not a real URL"
        },
        {
            "id": 9,
            "url": "http://netflix-payment-failed.scam-site.com",
            "ground_truth": "Phishing",
            "category": "Streaming Phishing",
            "note": "Example - not a real URL"
        },
        {
            "id": 10,
            "url": "http://google-security-check.fake-domain.com",
            "ground_truth": "Phishing",
            "category": "Search Engine Phishing",
            "note": "Example - not a real URL"
        }
    ]
}


class ConfusionMatrix:
    """Confusion Matrix for binary classification"""
    def __init__(self):
        self.true_positive = 0
        self.true_negative = 0
        self.false_positive = 0
        self.false_negative = 0
    
    def add_prediction(self, ground_truth: str, prediction: str):
        """Add a prediction to the confusion matrix"""
        is_phishing_truth = ground_truth.lower() in ['phishing', 'malicious']
        is_phishing_pred = prediction.lower() in ['phishing', 'malicious']
        
        if is_phishing_truth and is_phishing_pred:
            self.true_positive += 1
        elif not is_phishing_truth and not is_phishing_pred:
            self.true_negative += 1
        elif not is_phishing_truth and is_phishing_pred:
            self.false_positive += 1
        elif is_phishing_truth and not is_phishing_pred:
            self.false_negative += 1
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        total = self.true_positive + self.true_negative + self.false_positive + self.false_negative
        
        if total == 0:
            return None
        
        accuracy = (self.true_positive + self.true_negative) / total
        precision = self.true_positive / (self.true_positive + self.false_positive) if (self.true_positive + self.false_positive) > 0 else 0
        recall = self.true_positive / (self.true_positive + self.false_negative) if (self.true_positive + self.false_negative) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy * 100,
            'precision': precision * 100,
            'recall': recall * 100,
            'f1_score': f1_score * 100,
            'true_positive': self.true_positive,
            'true_negative': self.true_negative,
            'false_positive': self.false_positive,
            'false_negative': self.false_negative,
            'total_samples': total
        }
    
    def print_confusion_matrix(self):
        """Print confusion matrix"""
        print("\n" + "="*60)
        print("CONFUSION MATRIX")
        print("="*60)
        print(f"{'':20} | {'Predicted Phishing':20} | {'Predicted Legitimate':20}")
        print("-"*60)
        print(f"{'Actual Phishing':20} | {self.true_positive:20} | {self.false_negative:20}")
        print(f"{'Actual Legitimate':20} | {self.false_positive:20} | {self.true_negative:20}")
        print("="*60)


def simulate_predictions():
    """
    Simulate predictions for demo purposes
    In real evaluation, this would call your SafeClick API
    """
    print("\n" + "="*60)
    print("DEMO EVALUATION - Simulated Results")
    print("="*60)
    print("\nNOTE: This is a SIMULATION to demonstrate the process.")
    print("In real evaluation, each URL would be tested against your API.\n")
    
    confusion_matrix = ConfusionMatrix()
    results = []
    
    for sample in DEMO_DATASET['samples']:
        url = sample['url']
        ground_truth = sample['ground_truth']
        
        # Simulate prediction (in real evaluation, this calls your API)
        # For demo, we'll simulate high accuracy
        if 'suspicious-domain' in url or 'fake-site' in url or 'phishing-example' in url or 'scam-site' in url or 'fake-domain' in url:
            prediction = "Phishing"
            risk_score = 85
        else:
            prediction = "Legitimate"
            risk_score = 10
        
        print(f"[{sample['id']}/10] {url}")
        print(f"  Ground Truth: {ground_truth}")
        print(f"  Prediction: {prediction} (Risk: {risk_score})")
        print(f"  ✓ {'CORRECT' if (ground_truth == prediction) else 'INCORRECT'}\n")
        
        confusion_matrix.add_prediction(ground_truth, prediction)
        
        results.append({
            'id': sample['id'],
            'url': url,
            'ground_truth': ground_truth,
            'prediction': prediction,
            'risk_score': risk_score,
            'correct': ground_truth == prediction
        })
    
    return confusion_matrix, results


def print_metrics(metrics):
    """Print metrics"""
    if not metrics:
        print("No metrics to display")
        return
    
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)
    print(f"Accuracy:    {metrics['accuracy']:.2f}%")
    print(f"Precision:   {metrics['precision']:.2f}%")
    print(f"Recall:      {metrics['recall']:.2f}%")
    print(f"F1-Score:    {metrics['f1_score']:.2f}%")
    print("="*60)
    print(f"\nTotal Samples: {metrics['total_samples']}")
    print(f"True Positives:  {metrics['true_positive']}")
    print(f"True Negatives:  {metrics['true_negative']}")
    print(f"False Positives: {metrics['false_positive']}")
    print(f"False Negatives: {metrics['false_negative']}")
    print("="*60)


def save_demo_results(metrics, results):
    """Save demo results"""
    output = {
        'demo': True,
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'results': results,
        'note': 'This is a simulated demo. Run full evaluation with real API for actual metrics.'
    }
    
    filename = f"demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDemo results saved to: {filename}")


def main():
    """Main demo function"""
    print("="*60)
    print("SafeClick Demo Evaluation")
    print("="*60)
    print("\nThis is a DEMONSTRATION with 10 sample URLs.")
    print("For real evaluation, use collect_dataset.py and evaluate_model.py")
    print("="*60)
    
    # Save demo dataset
    with open('demo_dataset.json', 'w') as f:
        json.dump(DEMO_DATASET, f, indent=2)
    print("\n✓ Demo dataset saved to: demo_dataset.json")
    
    # Simulate evaluation
    confusion_matrix, results = simulate_predictions()
    
    # Calculate metrics
    metrics = confusion_matrix.calculate_metrics()
    
    # Print results
    confusion_matrix.print_confusion_matrix()
    print_metrics(metrics)
    
    # Save results
    save_demo_results(metrics, results)
    
    print("\n" + "="*60)
    print("NEXT STEPS FOR REAL EVALUATION")
    print("="*60)
    print("\n1. Collect real dataset:")
    print("   python collect_dataset.py")
    print("\n2. Update API endpoint in evaluate_model.py")
    print("\n3. Run full evaluation:")
    print("   python evaluate_model.py")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
