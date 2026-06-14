# 📊 SafeClick Model Evaluation

This directory contains tools to evaluate SafeClick's phishing detection performance and calculate metrics like Accuracy, Precision, Recall, and F1-Score.

---

## 🚀 Quick Start

### 1. Collect Test Dataset

```bash
cd evaluation
python collect_dataset.py
```

This will:
- Fetch 500 phishing URLs from PhishTank and OpenPhish
- Load 500 legitimate URLs from curated list
- Create `test_dataset.json` with 1,000 labeled samples

### 2. Configure API Endpoint

Edit `evaluate_model.py` and update:

```python
API_ENDPOINT = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod"
```

### 3. Run Evaluation

```bash
python evaluate_model.py
```

This will:
- Test all 1,000 URLs against SafeClick
- Calculate performance metrics
- Generate results files

### 4. View Results

Check the generated files:
- `evaluation_results_YYYYMMDD_HHMMSS.json` - Detailed results
- `metrics_YYYYMMDD_HHMMSS.csv` - Summary metrics

---

## 📁 Files

- **`collect_dataset.py`** - Collects phishing and legitimate URLs
- **`evaluate_model.py`** - Runs evaluation and calculates metrics
- **`test_dataset.json`** - Test dataset (generated)
- **`EVALUATION_GUIDE.md`** - Comprehensive evaluation guide

---

## 📊 Expected Metrics

Target performance (from your paper):
- **Accuracy**: 99.4%
- **Precision**: 99.2%
- **Recall**: 99.7%
- **F1-Score**: 99.4%

---

## 🔧 Requirements

```bash
pip install requests
```

---

## 📖 Documentation

See `EVALUATION_GUIDE.md` for:
- Detailed methodology
- Metric explanations
- Dataset sources
- Troubleshooting
- Performance optimization tips

---

## ⏱️ Estimated Time

- Dataset collection: 5-10 minutes
- Evaluation (1,000 URLs): 30-60 minutes
- Total: ~1 hour

---

## 💡 Tips

1. **Use fresh phishing URLs** - PhishTank updates daily
2. **Run multiple times** - Average results for consistency
3. **Analyze errors** - Investigate false positives/negatives
4. **Document findings** - Save results for your paper

---

## 🎯 Workflow

```
1. collect_dataset.py → test_dataset.json
2. evaluate_model.py → evaluation_results.json + metrics.csv
3. Analyze results → Include in paper
```

---

## ✅ Checklist

- [ ] Collect test dataset
- [ ] Configure API endpoint
- [ ] Run evaluation
- [ ] Review results
- [ ] Calculate metrics
- [ ] Compare with baseline
- [ ] Document findings

---

## 📞 Support

For detailed instructions, see `EVALUATION_GUIDE.md`
