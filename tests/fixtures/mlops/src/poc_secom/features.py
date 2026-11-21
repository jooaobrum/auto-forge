def build(df, drop=()):
    """Pure: DataFrame in, DataFrame out."""
    return df.drop(columns=list(drop))
