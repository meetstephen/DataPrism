"""Statistical analysis utilities: hypothesis tests, regression, and clustering."""
import pandas as pd
import numpy as np


def run_ttest(df, col, group_col, group_a, group_b):
    """Perform independent samples t-test.
    Returns dict with t_stat, p_value, verdict.
    """
    from scipy import stats

    group_a_data = df[df[group_col] == group_a][col].dropna()
    group_b_data = df[df[group_col] == group_b][col].dropna()

    if len(group_a_data) < 2 or len(group_b_data) < 2:
        return {"t_stat": None, "p_value": None, "verdict": "Insufficient data (need at least 2 samples per group)."}

    t_stat, p_value = stats.ttest_ind(group_a_data, group_b_data)

    if p_value < 0.01:
        verdict = f"Highly significant difference (p={p_value:.4f}). The means of '{group_a}' and '{group_b}' are very likely different."
    elif p_value < 0.05:
        verdict = f"Significant difference (p={p_value:.4f}). The means of '{group_a}' and '{group_b}' are likely different."
    else:
        verdict = f"No significant difference (p={p_value:.4f}). Cannot conclude the means differ."

    return {"t_stat": round(float(t_stat), 4), "p_value": round(float(p_value), 6), "verdict": verdict}


def run_chi_square(df, col_a, col_b):
    """Perform chi-square test of independence.
    Returns dict with chi2, p_value, dof, verdict.
    """
    from scipy import stats

    contingency = pd.crosstab(df[col_a], df[col_b])
    if contingency.size == 0:
        return {"chi2": None, "p_value": None, "dof": None, "verdict": "Cannot compute: empty contingency table."}

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    if p_value < 0.01:
        verdict = f"Highly significant association (p={p_value:.4f}). '{col_a}' and '{col_b}' are very likely related."
    elif p_value < 0.05:
        verdict = f"Significant association (p={p_value:.4f}). '{col_a}' and '{col_b}' are likely related."
    else:
        verdict = f"No significant association (p={p_value:.4f}). Cannot conclude the variables are related."

    return {"chi2": round(float(chi2), 4), "p_value": round(float(p_value), 6), "dof": int(dof), "verdict": verdict}


def run_anova(df, value_col, group_col):
    """Perform one-way ANOVA across groups.
    Returns dict with f_stat, p_value, verdict.
    """
    from scipy import stats

    groups = df[group_col].dropna().unique()
    group_data = [df[df[group_col] == g][value_col].dropna().values for g in groups]
    # Filter out groups with fewer than 2 observations
    group_data = [g for g in group_data if len(g) >= 2]

    if len(group_data) < 2:
        return {"f_stat": None, "p_value": None, "verdict": "Insufficient groups with enough data (need at least 2 groups with 2+ observations)."}

    f_stat, p_value = stats.f_oneway(*group_data)

    if p_value < 0.01:
        verdict = f"Highly significant difference between groups (p={p_value:.4f}). At least one group mean differs."
    elif p_value < 0.05:
        verdict = f"Significant difference between groups (p={p_value:.4f}). At least one group mean likely differs."
    else:
        verdict = f"No significant difference between groups (p={p_value:.4f}). Cannot conclude means differ."

    return {"f_stat": round(float(f_stat), 4), "p_value": round(float(p_value), 6), "verdict": verdict}


def run_linear_regression(df, x_cols, y_col):
    """Run linear regression.
    Returns dict with coefficients_df (DataFrame), r_squared, predictions (array).
    """
    from sklearn.linear_model import LinearRegression

    clean_df = df[x_cols + [y_col]].dropna()
    if len(clean_df) < 3:
        return {"coefficients_df": pd.DataFrame(), "r_squared": None, "predictions": np.array([])}

    X = clean_df[x_cols].values
    y = clean_df[y_col].values

    model = LinearRegression()
    model.fit(X, y)

    r_squared = round(float(model.score(X, y)), 4)
    predictions = model.predict(X)

    coef_data = {"Feature": x_cols, "Coefficient": [round(float(c), 4) for c in model.coef_]}
    coef_data["Feature"].append("Intercept")
    coef_data["Coefficient"].append(round(float(model.intercept_), 4))
    coefficients_df = pd.DataFrame(coef_data)

    return {"coefficients_df": coefficients_df, "r_squared": r_squared, "predictions": predictions}


def run_logistic_regression(df, x_cols, y_col):
    """Run logistic regression with label encoding.
    Returns dict with coefficients_df, accuracy, report (classification report text).
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, classification_report

    clean_df = df[x_cols + [y_col]].dropna()
    if len(clean_df) < 5:
        return {"coefficients_df": pd.DataFrame(), "accuracy": None, "report": "Insufficient data."}

    # Encode categorical X columns
    X_encoded = clean_df[x_cols].copy()
    encoders = {}
    for col in x_cols:
        if X_encoded[col].dtype == object:
            le = LabelEncoder()
            X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
            encoders[col] = le

    # Encode y
    le_y = LabelEncoder()
    y_encoded = le_y.fit_transform(clean_df[y_col].astype(str))

    X = X_encoded.values
    y = y_encoded

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)

    predictions = model.predict(X)
    accuracy = round(float(accuracy_score(y, predictions)), 4)
    report = classification_report(y, predictions, target_names=[str(c) for c in le_y.classes_])

    coef_data = {"Feature": list(x_cols), "Coefficient": [round(float(c), 4) for c in model.coef_[0]]}
    coefficients_df = pd.DataFrame(coef_data)

    return {"coefficients_df": coefficients_df, "accuracy": accuracy, "report": report}


def run_kmeans_clustering(df, columns, max_k=10):
    """Run K-Means clustering with elbow method.
    Returns dict with labels, inertias, cluster_stats, optimal_k.
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    clean_df = df[columns].dropna()
    if len(clean_df) < 4:
        return {"labels": np.array([]), "inertias": [], "cluster_stats": pd.DataFrame(), "optimal_k": 2}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(clean_df)

    max_k = min(max_k, len(clean_df) - 1)
    if max_k < 2:
        max_k = 2

    inertias = []
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(float(km.inertia_))

    # Pick optimal k using elbow heuristic (largest drop in inertia)
    optimal_k = 2
    if len(inertias) > 2:
        diffs = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
        second_diffs = [diffs[i] - diffs[i + 1] for i in range(len(diffs) - 1)]
        if second_diffs:
            elbow_idx = np.argmax(second_diffs) + 2  # +2 because k starts at 2
            optimal_k = elbow_idx

    # Fit with optimal k
    final_km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = final_km.fit_predict(X_scaled)

    # Per-cluster stats (means of original values)
    clean_df = clean_df.copy()
    clean_df["cluster"] = labels
    cluster_stats = clean_df.groupby("cluster")[columns].mean().round(2)

    return {
        "labels": labels,
        "inertias": inertias,
        "cluster_stats": cluster_stats,
        "optimal_k": int(optimal_k),
    }


def ai_describe_clusters(cluster_stats, api_key):
    """Use Gemini to describe each cluster in plain English.
    Returns (text, error).
    """
    try:
        from utils.ai_client import generate_content

        if isinstance(cluster_stats, pd.DataFrame):
            stats_text = cluster_stats.to_string()
        else:
            stats_text = str(cluster_stats)

        prompt = f"""Given these cluster statistics (mean values per cluster per feature),
describe each cluster in 2-3 sentences of plain English. What characterizes each group?
Give each cluster a descriptive name.

Cluster Statistics:
{stats_text}

Format: For each cluster, provide a name and description."""

        system = "You are a data science expert. Be concise and insightful."
        text, err = generate_content(prompt, api_key=api_key, system_instruction=system)
        return text, err
    except Exception as e:
        return None, f"Cluster description failed: {str(e)}"
