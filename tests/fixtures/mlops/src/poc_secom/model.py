from sklearn.linear_model import LogisticRegression

def fit(X, y, seed=42):
    return LogisticRegression(max_iter=1000, random_state=seed).fit(X, y)
