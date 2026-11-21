from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

TASK = "binary"
DROP = []

def prepare(df):
    return df

def build_pipeline():
    return make_pipeline(SimpleImputer(), StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
