"""
SafeClick Model Evaluation Script
Calculates Accuracy, Precision, Recall, and F1-Score

This script tests SafeClick against a labeled dataset and computes performance metrics.
"""

import json
import time
import requests
from typing import Dict, List, Tuple
from datetime import datetime
import csv

# Configuration
API_ENDPOINT = "https://2creda2yj3.execute-api.us-east-1.amazonaws.com/dev"
TEST_DATASET_FILE = "test_dataset.json"
RESULTS_FILE = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
METRICS_FILE = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# Delay between requests to avoid rate limiting
REQUEST_DELAY = 2  # seconds


class ConfusionMatrix:
    """Confusion Matrix for binary classification"""
    def __init__(self):
        self.true_positive = 0   # Correctly identified phishing
        self.true_negative = 0   # Correctly identified legitimate
        self.false_positive = 0  # Legitimate marked as phishing
        self.false_negative = 0  # Phishing marked as legitimate
    
    def add_prediction(self, ground_truth: str, prediction: str):
        """Add a prediction to the confusion matrix"""
        # Normalize verdicts
        is_phishing_truth = ground_truth.lower() in ['phishing', 'malicious', 'fake']
        is_phishing_pred = prediction.lower() in ['phishing', 'malicious']
        
        if is_phishing_truth and is_phishing_pred:
            self.true_positive += 1
        elif not is_phishing_truth and not is_phishing_pred:
            self.true_negative += 1
        elif not is_phishing_truth and is_phishing_pred:
            self.false_positive += 1
        elif is_phishing_truth and not is_phishing_pred:
            self.false_negative += 1
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        total = self.true_positive + self.true_negative + self.false_positive + self.false_negative
        
        # Accuracy: (TP + TN) / Total
        accuracy = (self.true_positive + self.true_negative) / total if total > 0 else 0
        
        # Precision: TP / (TP + FP)
        precision = self.true_positive / (self.true_positive + self.false_positive) if (self.true_positive + self.false_positive) > 0 else 0
        
        # Recall (Sensitivity): TP / (TP + FN)
        recall = self.true_positive / (self.true_positive + self.false_negative) if (self.true_positive + self.false_negative) > 0 else 0
        
        # F1-Score: 2 * (Precision * Recall) / (Precision + Recall)
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Specificity: TN / (TN + FP)
        specificity = self.true_negative / (self.true_negative + self.false_positive) if (self.true_negative + self.false_positive) > 0 else 0
        
        return {
            'accuracy': accuracy * 100,
            'precision': precision * 100,
            'recall': recall * 100,
            'f1_score': f1_score * 100,
            'specificity': specificity * 100,
            'true_positive': self.true_positive,
            'true_negative': self.true_negative,
            'false_positive': self.false_positive,
            'false_negative': self.false_negative,
            'total_samples': total
        }
    
    def print_confusion_matrix(self):
        """Print confusion matrix in readable format"""
        print("\n" + "="*60)
        print("CONFUSION MATRIX")
        print("="*60)
        print(f"{'':20} | {'Predicted Phishing':20} | {'Predicted Legitimate':20}")
        print("-"*60)
        print(f"{'Actual Phishing':20} | {self.true_positive:20} | {self.false_negative:20}")
        print(f"{'Actual Legitimate':20} | {self.false_positive:20} | {self.true_negative:20}")
        print("="*60)


def load_test_dataset(filename: str) -> List[Dict]:
    """Load test dataset from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data.get('samples', [])


def scan_url(url: str) -> Dict:
    """Scan a URL using SafeClick API"""
    try:
        # Submit URL for scanning
        response = requests.post(
            f"{API_ENDPOINT}/analyze",
            json={"url": url},
            timeout=30
        )
        response.raise_for_status()
        
        # Wait for analysis to complete
        time.sleep(15)  # Typical analysis time
        
        # Get results
        results_response = requests.get(
            f"{API_ENDPOINT}/results",
            params={"url": url},
            timeout=30
        )
        results_response.raise_for_status()
        
        result = results_response.json()
        return {
            'verdict': result.get('verdict', 'Unknown'),
            'riskScore': result.get('riskScore', 0),
            'confidence': result.get('confidence', 'Low'),
            'explanation': result.get('explanation', ''),
            'processingTimeMs': result.get('processingTimeMs', 0)
        }
    
    except Exception as e:
        print(f"Error scanning {url}: {str(e)}")
        return {
            'verdict': 'Error',
            'riskScore': 0,
            'confidence': 'Low',
            'explanation': str(e),
            'processingTimeMs': 0
        }


def evaluate_model(dataset: List[Dict]) -> Tuple[ConfusionMatrix, List[Dict]]:
    """Evaluate model on test dataset"""
    confusion_matrix = ConfusionMatrix()
    detailed_results = []
    
    total = len(dataset)
    print(f"\nStarting evaluation on {total} samples...")
    print("="*60)
    
    for idx, sample in enumerate(dataset, 1):
        url = sample['url']
        ground_truth = sample['ground_truth']
        
        print(f"\n[{idx}/{total}] Testing: {url}")
        print(f"Ground Truth: {ground_truth}")
        
        # Scan URL
        result = scan_url(url)
        prediction = result['verdict']
        
        print(f"Prediction: {prediction} (Risk: {result['riskScore']}, Confidence: {result['confidence']})")
        
        # Update confusion matrix
        confusion_matrix.add_prediction(ground_truth, prediction)
        
        # Store detailed result
        detailed_results.append({
            'id': sample['id'],
            'url': url,
            'ground_truth': ground_truth,
            'prediction': prediction,
            'risk_score': result['riskScore'],
            'confidence': result['confidence'],
            'correct': (ground_truth.lower() in ['phishing', 'malicious']) == (prediction.lower() in ['phishing', 'malicious']),
            'processing_time_ms': result['processingTimeMs']
        })
        
        # Delay between requests
        if idx < total:
            time.sleep(REQUEST_DELAY)
    
    return confusion_matrix, detailed_results


def save_results(metrics: Dict, detailed_results: List[Dict]):
    """Save evaluation results to files"""
    # Save detailed results
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            'metrics': metrics,
            'detailed_results': detailed_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {RESULTS_FILE}")
    
    # Save metrics to CSV
    with open(METRICS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        for key, value in metrics.items():
            if isinstance(value, float):
                writer.writerow([key.replace('_', ' ').title(), f"{value:.2f}%"])
            else:
                writer.writerow([key.replace('_', ' ').title(), value])
    
    print(f"Metrics saved to: {METRICS_FILE}")


def print_metrics(metrics: Dict):
    """Print metrics in readable format"""
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)
    print(f"Accuracy:    {metrics['accuracy']:.2f}%")
    print(f"Precision:   {metrics['precision']:.2f}%")
    print(f"Recall:      {metrics['recall']:.2f}%")
    print(f"F1-Score:    {metrics['f1_score']:.2f}%")
    print(f"Specificity: {metrics['specificity']:.2f}%")
    print("="*60)
    print(f"\nTotal Samples: {metrics['total_samples']}")
    print(f"True Positives:  {metrics['true_positive']}")
    print(f"True Negatives:  {metrics['true_negative']}")
    print(f"False Positives: {metrics['false_positive']}")
    print(f"False Negatives: {metrics['false_negative']}")
    print("="*60)


def main():
    """Main evaluation function"""
    print("="*60)
    print("SafeClick Model Evaluation")
    print("="*60)
    
    # Load test dataset
    print(f"\nLoading test dataset from {TEST_DATASET_FILE}...")
    dataset = load_test_dataset(TEST_DATASET_FILE)
    print(f"Loaded {len(dataset)} samples")
    
    # Evaluate model
    confusion_matrix, detailed_results = evaluate_model(dataset)
    
    # Calculate metrics
    metrics = confusion_matrix.calculate_metrics()
    
    # Print results
    confusion_matrix.print_confusion_matrix()
    print_metrics(metrics)
    
    # Save results
    save_results(metrics, detailed_results)
    
    print("\n" + "="*60)
    print("Evaluation Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
