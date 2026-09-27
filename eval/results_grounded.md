# Eval Results: Groq GROUNDED (real pipeline)

- **Dataset size**: 25 labeled task pairs
- **Precision**: 100.00%
- **Recall**: 100.00%
- **F1 Score**: 100.00%
- **Accuracy**: 100.00%
- **Confusion**: TP=13 FP=0 FN=0 TN=12

## Per-item results

| ID | Actual | Predicted | Outcome | Confidence | Existing Task | New Task |
|---|---|---|---|---|---|---|
| 1 | True | True | TP | 95 | Design database schema | Build REST API |
| 2 | True | True | TP | 100 | Set up CI pipeline | Deploy to production |
| 3 | True | True | TP | 95 | Write authentication middleware | Build user profile page |
| 4 | True | True | TP | 95 | Create wireframes | Implement checkout UI |
| 5 | True | True | TP | 95 | Procure server hardware | Install OS on servers |
| 6 | True | True | TP | 95 | Foundation work | Build walls |
| 7 | True | True | TP | 95 | Electrical wiring | Install drywall |
| 8 | True | True | TP | 95 | Write unit tests for payment module | Release payment module to staging |
| 9 | True | True | TP | 95 | Get legal approval for contract terms | Sign vendor contract |
| 10 | True | True | TP | 95 | Collect customer requirements | Write technical spec |
| 11 | True | True | TP | 95 | Train the ML model | Deploy model to production |
| 12 | True | True | TP | 95 | Purchase domain name | Configure DNS records |
| 13 | True | True | TP | 95 | Design app logo | Add logo to app header |
| 14 | False | False | TN | - | Design database schema | Write marketing copy |
| 15 | False | False | TN | - | Set up CI pipeline | Plan team offsite |
| 16 | False | False | TN | - | Foundation work | Choose paint colors |
| 17 | False | False | TN | - | Write unit tests for payment module | Design employee onboarding doc |
| 18 | False | False | TN | - | Train the ML model | Renew office lease |
| 19 | False | False | TN | - | Purchase domain name | Design app logo |
| 20 | False | False | TN | - | Electrical wiring | Order kitchen appliances |
| 21 | False | False | TN | - | Get legal approval for contract terms | Organize company picnic |
| 22 | False | False | TN | - | Collect customer requirements | Fix office printer |
| 23 | False | False | TN | - | Create wireframes | Renew SSL certificate |
| 24 | False | False | TN | - | Procure server hardware | Write API documentation |
| 25 | False | False | TN | - | Write authentication middleware | Choose office furniture |