"""
Synthetic data generator for community college dataset.
Generates ~800 rows of realistic student data.
"""

import numpy as np
import pandas as pd
import os


def generate_dataset(seed=42):
    """
    Generate a realistic synthetic community college dataset.

    Returns:
        pd.DataFrame: DataFrame with ~800 rows of student data.
    """
    np.random.seed(seed)

    num_rows = 800

    # Define data options
    majors = [
        "Computer Science", "Business", "Biology", "Psychology",
        "English", "Mathematics", "Nursing", "Engineering"
    ]

    years = [2020, 2021, 2022, 2023]

    professors = [
        "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez",
        "Dr. James Williams", "Dr. Maria Garcia", "Dr. Robert Taylor",
        "Dr. Lisa Anderson", "Dr. David Martinez", "Dr. Jennifer Brown",
        "Dr. Thomas Wilson", "Dr. Patricia Davis", "Dr. Christopher Lee",
        "Dr. Amanda Thompson", "Dr. Daniel Harris", "Dr. Michelle Clark",
        "Dr. Kevin White", "Dr. Susan Hall"
    ]

    courses_by_major = {
        "Computer Science": ["Intro to Programming", "Data Structures", "Algorithms",
                             "Database Systems", "Web Development"],
        "Business": ["Principles of Management", "Business Ethics", "Marketing 101",
                     "Financial Accounting", "Entrepreneurship"],
        "Biology": ["General Biology", "Microbiology", "Anatomy & Physiology",
                    "Genetics", "Ecology"],
        "Psychology": ["Intro to Psychology", "Developmental Psychology",
                       "Abnormal Psychology", "Social Psychology"],
        "English": ["English Composition", "Creative Writing",
                    "American Literature", "Technical Writing"],
        "Mathematics": ["Calculus I", "Statistics", "Linear Algebra",
                        "Discrete Mathematics"],
        "Nursing": ["Fundamentals of Nursing", "Pharmacology",
                    "Health Assessment", "Clinical Practicum"],
        "Engineering": ["Engineering Physics", "Circuit Analysis",
                        "Thermodynamics", "Engineering Design"]
    }

    cost_ranges_by_major = {
        "Computer Science": (1200, 4000),
        "Business": (1000, 3500),
        "Biology": (1500, 4500),
        "Psychology": (800, 3000),
        "English": (500, 2500),
        "Mathematics": (800, 3000),
        "Nursing": (2000, 5000),
        "Engineering": (1500, 4500)
    }

    first_names = [
        "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
        "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
        "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Abigail", "Daniel",
        "Emily", "Matthew", "Elizabeth", "Jackson", "Sofia", "Sebastian", "Avery",
        "Jack", "Ella", "Aiden", "Scarlett", "Owen", "Grace", "Samuel", "Chloe",
        "Ryan", "Victoria", "Nathan", "Riley", "Caleb", "Aria", "Christian",
        "Lily", "Dylan", "Aurora", "Isaac", "Zoey", "Andrew"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
        "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
        "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
    ]

    # Generate data
    student_ids = [f"STU-{i+1:04d}" for i in range(num_rows)]

    student_names = [
        f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
        for _ in range(num_rows)
    ]

    selected_majors = np.random.choice(majors, size=num_rows).tolist()

    selected_years = np.random.choice(years, size=num_rows).tolist()

    # Student type: ~65% full-time, ~35% part-time
    student_types = np.random.choice(
        ["Full-time", "Part-time"],
        size=num_rows,
        p=[0.65, 0.35]
    ).tolist()

    selected_professors = np.random.choice(professors, size=num_rows).tolist()

    # Select courses based on major
    selected_courses = []
    for major in selected_majors:
        course = np.random.choice(courses_by_major[major])
        selected_courses.append(course)

    # Generate course costs based on major
    course_costs = []
    for major in selected_majors:
        low, high = cost_ranges_by_major[major]
        cost = round(np.random.uniform(low, high), 2)
        course_costs.append(cost)

    # Generate evaluation scores (1.0 - 5.0)
    evaluation_scores = np.round(
        np.clip(np.random.normal(3.5, 0.8, num_rows), 1.0, 5.0), 1
    ).tolist()

    df = pd.DataFrame({
        "Student_ID": student_ids,
        "Student_Name": student_names,
        "Major": selected_majors,
        "Year": selected_years,
        "Student_Type": student_types,
        "Professor": selected_professors,
        "Course": selected_courses,
        "Course_Cost": course_costs,
        "Evaluation_Score": evaluation_scores
    })

    return df


def save_dataset(filepath="data/community_college_data.csv"):
    """
    Generate and save the synthetic dataset to a CSV file.

    Args:
        filepath (str): Path where the CSV file will be saved.

    Returns:
        pd.DataFrame: The generated dataset.
    """
    df = generate_dataset()

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    df.to_csv(filepath, index=False)
    return df


if __name__ == "__main__":
    df = save_dataset()
    print(f"Dataset generated: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {df.columns.tolist()}")
