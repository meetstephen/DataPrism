"""Statistical tests and machine learning utilities for DataPrism."""
import pandas as pd
import numpy as np


def run_ttest(df, column, group_col, group_a, group_b):
    """Run an independent samples t-test between two groups.

    Returns a dict with keys: t_statistic, p_value, mean_a, mean_b, significant.
    """
    from scipy import stats

    a = df[df[group_col] == group_a][column].dropna()
    b = df[df[group_col] == group_b][column].dropna()

    if len(a) < 2 or len(b) < 2:
        return {"error": "Each group needs at least 2 observations."}

    t_stat, p_val = stats.ttest_ind(a, b)
    return {
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_val), 6),
        "mean_a": round(float(a.mean()), 4),
        "mean_b": round(float(b.mean()), 4),
        "n_a": len(a),
        "n_b": len(b),
        "significant": p_val < 0.05,
    }


def run_chi_square(df, col_a, col_b):
    """Run a chi-square test of independence between two categorical columns.

    Returns a dict with keys: chi2, p_value, dof, significant, contingency_table.
    """
    from scipy import stats

    contingency = pd.crosstab(df[col_a], df[col_b])
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return {"error": "Need at least 2 categories in each column."}

    chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
    return {
        "chi2": round(float(chi2), 4),
        "p_value": round(float(p_val), 6),
        "dof": int(dof),
        "significant": p_val < 0.05,
        "contingency_table": contingency.to_dict(),
    }


def run_anova(df, value_col, group_col):
    """Run one-way ANOVA across groups defined by group_col.

    Returns a dict with keys: f_statistic, p_value, group_means, significant.
    """
    from scipy import stats

    groups = []
    group_names = df[group_col].dropna().unique()
    group_means = {}

    for name in group_names:
        vals = df[df[group_col] == name][value_col].dropna()
        if len(vals) >= 2:
            groups.append(vals.values)
            group_means[str(name)] = round(float(vals.mean()), 4)

    if len(groups) < 2:
        return {"error": "Need at least 2 groups with 2+ observations each."}

    f_stat, p_val = stats.f_oneway(*groups)
    return {
        "f_statistic": round(float(f_stat), 4),
        "p_value": round(float(p_val), 6),
        "n_groups": len(groups),
        "group_means": group_means,
        "significant": p_val < 0.05,
    }


def run_linear_regression(df, target_col, feature_cols):
    """Run OLS linear regression.

    Returns a dict with keys: coefficients, r_squared, adj_r_squared, p_values, residuals_summary.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    clean = df[feature_cols + [target_col]].dropna()
    if len(clean) < len(feature_cols) + 2:
        return {"error": "Not enough observations for regression."}

    X = clean[feature_cols].values
    y = clean[target_col].values

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    r2 = r2_score(y, y_pred)
    n = len(y)
    p = len(feature_cols)
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2

    coefficients = {}
    coefficients["intercept"] = round(float(model.intercept_), 4)
    for i, col in enumerate(feature_cols):
        coefficients[col] = round(float(model.coef_[i]), 4)

    residuals = y - y_pred
    return {
        "coefficients": coefficients,
        "r_squared": round(float(r2), 4),
        "adj_r_squared": round(float(adj_r2), 4),
        "n_observations": n,
        "residuals_mean": round(float(residuals.mean()), 6),
        "residuals_std": round(float(residuals.std()), 4),
    }


def run_logistic_regression(df, target_col, feature_cols):
    """Run logistic regression for binary classification.

    Returns a dict with keys: coefficients, accuracy, classes.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import LabelEncoder

    clean = df[feature_cols + [target_col]].dropna()
    if len(clean) < 10:
        return {"error": "Need at least 10 observations for logistic regression."}

    X = clean[feature_cols].values
    y_raw = clean[target_col]

    # Encode target if not numeric
    if not pd.api.types.is_numeric_dtype(y_raw):
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
        classes = le.classes_.tolist()
    else:
        y = y_raw.values
        classes = sorted(pd.unique(y).tolist())

    if len(set(y)) < 2:
        return {"error": "Target must have at least 2 classes."}

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)

    coefficients = {}
    coefficients["intercept"] = round(float(model.intercept_[0]), 4) if len(model.intercept_) > 0 else 0
    for i, col in enumerate(feature_cols):
        coef_val = model.coef_[0][i] if model.coef_.ndim > 1 else model.coef_[i]
        coefficients[col] = round(float(coef_val), 4)

    return {
        "coefficients": coefficients,
        "accuracy": round(float(acc), 4),
        "n_observations": len(y),
        "classes": [str(c) for c in classes],
    }


def run_kmeans_clustering(df, feature_cols, n_clusters=3):
    """Run K-Means clustering.

    Returns a dict with keys: labels (list), centers (list of dicts), inertia.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    clean = df[feature_cols].dropna()
    if len(clean) < n_clusters:
        return {"error": f"Need at least {n_clusters} observations for {n_clusters} clusters."}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(clean.values)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X_scaled)

    # Inverse transform centers
    centers_original = scaler.inverse_transform(model.cluster_centers_)
    centers = []
    for i, center in enumerate(centers_original):
        center_dict = {"cluster": i}
        for j, col in enumerate(feature_cols):
            center_dict[col] = round(float(center[j]), 4)
        centers.append(center_dict)

    return {
        "labels": labels.tolist(),
        "centers": centers,
        "inertia": round(float(model.inertia_), 4),
        "n_clusters": n_clusters,
        "n_observations": len(clean),
        "feature_cols": feature_cols,
    }


def ai_describe_clusters(cluster_result, api_key=None):
    """Use AI to describe cluster characteristics in plain language.

    Returns a string description.
    """
    try:
        from utils.ai_client import generate_content, get_api_key

        key = api_key or get_api_key()
        if not key:
            return _rule_based_cluster_description(cluster_result)

        centers = cluster_result.get("centers", [])
        prompt = (
            "You are a data analyst. Describe these K-Means cluster centers in "
            "plain language (2-3 sentences per cluster). What characterizes each group?\n\n"
            f"Clusters:\n{centers}\n"
        )
        text, err = generate_content(prompt, api_key=key)
        if text:
            return text
        return _rule_based_cluster_description(cluster_result)
    except Exception:
        return _rule_based_cluster_description(cluster_result)


def _rule_based_cluster_description(cluster_result):
    """Fallback rule-based cluster description."""
    centers = cluster_result.get("centers", [])
    if not centers:
        return "No cluster information available."

    parts = []
    for center in centers:
        cluster_id = center.get("cluster", 0)
        features = {k: v for k, v in center.items() if k != "cluster"}
        high_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:3]
        desc = ", ".join([f"{k}={v}" for k, v in high_features])
        parts.append(f"Cluster {cluster_id}: Characterized by {desc}")

    return "\n".join(parts)
