import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="SBU-COL Juris Doctor QPI Calculator",
    layout="wide"
)

# -------------------------------
# CUSTOM FONTS
# -------------------------------
st.markdown("""
    <style>
    h1, h2, h3 { font-family: 'Arial', sans-serif; }
    p, div, span { font-family: 'Tahoma', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# LOAD CURRICULUM
# -------------------------------
@st.cache_data
def load_curriculum():
    df = pd.read_csv("curriculum.csv", quotechar='"')
    df["Grade"] = None  # initialize grades as empty
    return df

curriculum = load_curriculum()

st.title("COL Juris Doctor QPI Calculator")
st.caption("*Unofficial calculator based on the 2021 SBU-COL handbook.*")
st.markdown("---")

# -------------------------------
# LAYOUT: LEFT = CURRICULUM, RIGHT = QPI DASHBOARD
# -------------------------------
left_col, right_col = st.columns([3, 1])

# -------------------------------
# LEFT: CURRICULUM TABLE
# -------------------------------
with left_col:
    st.header("Juris Doctor (Non-Thesis)")
    curriculum_grades = curriculum.copy()
    year_qpis = {}

    for year, year_df in curriculum_grades.groupby("Year"):
        with st.expander(f"{year}", expanded=True):
            for sem, sem_df in year_df.groupby("Semester"):
                # Highlight grades below 75
                def highlight_grade(val):
                    if val is None or pd.isna(val):
                        return ""
                    return "color: red;" if val < 75 else ""
                
                edited_sem = st.data_editor(
                    sem_df.style.applymap(highlight_grade, subset=["Grade"]),
                    column_config={
                        "Grade": st.column_config.NumberColumn(
                            "Grade",
                            min_value=65.0,
                            max_value=100.0,
                            step=0.5
                        )
                    },
                    hide_index=True,
                )
                curriculum_grades.loc[edited_sem.index, "Grade"] = edited_sem["Grade"]

            # Calculate cumulative QPI up to this year
            completed_subjects = curriculum_grades[
                curriculum_grades["Grade"].notna() & (curriculum_grades["Grade"] > 0)
            ]
            cumulative_units = completed_subjects["Units"].sum()
            cumulative_weighted_sum = (completed_subjects["Units"] * completed_subjects["Grade"]).sum()
            year_qpi = cumulative_weighted_sum / cumulative_units if cumulative_units > 0 else 0
            year_qpis[year] = year_qpi

# -------------------------------
# RIGHT: QPI DASHBOARD
# -------------------------------
with right_col:
    st.header("QPI Summary")

    # Completed grades only
    completed_subjects = curriculum_grades[
        curriculum_grades["Grade"].notna() & (curriculum_grades["Grade"] > 0)
    ]
    total_units_completed = completed_subjects["Units"].sum()
    weighted_sum_completed = (completed_subjects["Units"] * completed_subjects["Grade"]).sum()
    cumulative_qpi = weighted_sum_completed / total_units_completed if total_units_completed > 0 else 0

    # Total units
    total_units = curriculum_grades["Units"].sum()
    remaining_units_total = total_units - total_units_completed
    completion_pct = (total_units_completed / total_units * 100) if total_units > 0 else 0

    # Display summary
    st.markdown(f"### Cumulative QPI: **{cumulative_qpi:.2f}**")
    st.markdown(f"**Total Units Taken:** {total_units_completed}")
    st.markdown(f"**Total Units Left:** {remaining_units_total}")
    st.progress(int(completion_pct))
    st.markdown(f"**{completion_pct:.0f}% Complete ({total_units_completed}/{total_units})**")

    st.markdown("---")
    st.header("Target QPI Calculator")

    # ---------------------------
    # Target QPI Calculator with Scope
    # ---------------------------
    st.header("Target QPI Calculator")

    # Scope selection
    scope = st.selectbox("Select Scope", ["1L", "2L", "3L", "4L", "TOTAL"])

    # Filter the curriculum based on scope
    if scope == "TOTAL":
        scope_df = curriculum_grades.copy()
    else:
        scope_df = curriculum_grades[curriculum_grades["Year"] == scope]

    # Total points completed in the scope
    completed_scope = scope_df[scope_df["Grade"].notna() & (scope_df["Grade"] > 0)]
    current_points = (completed_scope["Units"] * completed_scope["Grade"]).sum()
    graded_units = completed_scope["Units"].sum()

    # Remaining units in the scope
    remaining_scope_df = scope_df[scope_df["Grade"].isna() | (scope_df["Grade"] == 0)]
    remaining_units = remaining_scope_df["Units"].sum()

    # Target QPI input
    target_qpi = st.number_input("Target QPI", min_value=65.0, max_value=100.0, value=75.0, step=0.5)

    # Total units in scope
    total_units_scope = graded_units + remaining_units
    total_points_needed = target_qpi * total_units_scope
    points_deficit = total_points_needed - current_points

    # ---------------------------
    # Logic for required average
    # ---------------------------
    MAX_GRADE = 100

    if remaining_units > 0:
        required_avg = points_deficit / remaining_units
        if required_avg > MAX_GRADE:
            st.error(f"Target QPI of {target_qpi:.2f} is not possible in {scope}. Requires average > {MAX_GRADE:.2f}.")
        elif required_avg <= 0:
            st.success(f"Target QPI of {target_qpi:.2f} is already secured in {scope}! You will reach it even with minimum grades.")
        else:
            st.info(f"Required average grade for remaining units in {scope} to reach **{target_qpi:.2f}**: **{required_avg:.2f}**")
    else:
        # No remaining units in scope
        final_qpi = current_points / graded_units if graded_units > 0 else 0
        if final_qpi >= target_qpi:
            st.success(f"Target QPI of {target_qpi:.2f} reached in {scope}! Final QPI: {final_qpi:.2f}")
        else:
            st.error(f"Target QPI of {target_qpi:.2f} missed in {scope}. Final QPI: {final_qpi:.2f}")

    # -------------------------------
    # COURSE GRADE CALCULATOR
    # -------------------------------
    st.markdown("---")
    st.header("Course Grade Calculator")

    # Default components
    default_components = [
        {"Label": "Midterm Standing", "Weight": 16.67, "Score": None},
        {"Label": "Midterm Exam", "Weight": 16.67, "Score": None},
        {"Label": "Finals Standing", "Weight": 33.33, "Score": None},
        {"Label": "Final Exam", "Weight": 33.33, "Score": None},
    ]

    if "components" not in st.session_state:
        st.session_state.components = default_components

    components_df = pd.DataFrame(st.session_state.components)

    # Editable table
    edited_components = st.data_editor(
        components_df,
        column_config={
            "Label": st.column_config.TextColumn("Component"),
            "Weight": st.column_config.NumberColumn("Weight (%)", min_value=0.0, max_value=100.0, step=0.01),
            "Score": st.column_config.NumberColumn("My Score", min_value=65.0, max_value=100.0, step=0.5),
        },
        hide_index=True,
        key="course_grade_editor_nan_safe"
    )
    st.session_state.components = edited_components.to_dict(orient="records")

    # Target grade input
    target_grade = st.number_input("Target Final Grade", min_value=65.0, max_value=100.0, value=90.0, step=0.5)

    # -------------------------------
    # Calculation
    # -------------------------------
    MAX_GRADE = 100
    MIN_GRADE = 65

    current_weighted_points = 0
    total_weight_used = 0

    for comp in st.session_state.components:
        score = comp["Score"]
        weight = comp["Weight"]

        # --- SANITIZATION STEP ---
        if pd.isna(score) or score is None:
            continue  # skip empty or NaN cells

        # Safe conversion
        try:
            score_val = float(score)
        except:
            continue  # skip invalid entries

        # --- MATH LOGIC ---
        current_weighted_points += score_val * (weight / 100)
        total_weight_used += weight

    # Scenario A: Current Standing
    if total_weight_used > 0:
        current_grade = current_weighted_points / (total_weight_used / 100)
    else:
        current_grade = 0  # No graded components yet

    st.markdown(f"Current Standing: **{current_grade:.2f}%** based on {total_weight_used:.2f}% of total weight")

    # Scenario B: Projection for remaining components
    remaining_weight = 100 - total_weight_used

    if remaining_weight > 0:
        points_needed = target_grade - current_weighted_points
        required_score = points_needed / (remaining_weight / 100)

        if required_score > MAX_GRADE:
            st.error(f"Target grade of {target_grade:.2f}% is impossible. Requires average > {MAX_GRADE:.2f}% for remaining components.")
        elif required_score <= MIN_GRADE:
            st.success(f"Target grade of {target_grade:.2f}% already secured! Even minimum grades will reach it.")
        else:
            st.info(f"Required average for remaining components to reach **{target_grade:.2f}%**: **{required_score:.2f}%**")
    else:
        # No remaining components
        final_grade = current_weighted_points
        if final_grade >= target_grade:
            st.success(f"Final Grade: {final_grade:.2f}%. Target of {target_grade:.2f}% reached!")
        else:
            st.error(f"Final Grade: {final_grade:.2f}%. Target of {target_grade:.2f}% missed.")

st.markdown("---")
st.caption("⚠️ This tool is for estimation only and does not replace official evaluation by SBU-COL.")
