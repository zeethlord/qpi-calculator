import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(
    page_title="SBU-COL JD QPI Dashboard",
    layout="wide"
)

# -------------------------------
# LOAD CURRICULUM
# -------------------------------
@st.cache_data
def load_curriculum():
    df = pd.read_csv("curriculum.csv", quotechar='"')
    # initialize grades as empty strings for better data_editor behavior
    df["Grade"] = np.nan
    return df

curriculum = load_curriculum()

st.title("Quality Point Index Calculator for Juris Doctor (Non-Thesis)")
st.caption("*Unofficial estimator based on the SBU-COL 2021 handbook*")
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

    # Store cumulative QPIs per year
    year_qpis = {}

    for year, year_df in curriculum_grades.groupby("Year"):
        with st.expander(f"{year}", expanded=True):
            for sem, sem_df in year_df.groupby("Semester"):
                # Highlight grades below 75
                def highlight_grade(val):
                    if pd.isna(val):
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
                    hide_index=True
                )
                curriculum_grades.loc[edited_sem.index, "Grade"] = edited_sem["Grade"]

            # Calculate cumulative QPI up to this year using only entered grades >0
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

    # Only include grades entered by user
    completed_subjects = curriculum_grades[
        curriculum_grades["Grade"].notna() & (curriculum_grades["Grade"] > 0)
    ]
    total_units_completed = completed_subjects["Units"].sum()
    weighted_sum_completed = (completed_subjects["Units"] * completed_subjects["Grade"]).sum()
    cumulative_qpi = weighted_sum_completed / total_units_completed if total_units_completed > 0 else 0

    # Total units
    total_units = curriculum_grades["Units"].sum()
    remaining_units = total_units - total_units_completed
    completion_pct = (total_units_completed / total_units * 100) if total_units > 0 else 0

    # Display metrics
    st.markdown(f"### Cumulative QPI: **{cumulative_qpi:.2f}**")
    st.markdown(f"**Total Units Taken:** {total_units_completed}")
    st.markdown(f"**Total Units Left:** {remaining_units}")
    st.progress(int(completion_pct))
    st.markdown(f"**{completion_pct:.0f}% Complete ({total_units_completed}/{total_units})**")

    st.markdown("---")
    st.header("Target QPI")

    target_qpi = st.number_input("Target QPI", min_value=65.0, max_value=100.0, value=75.0, step=0.5)

    if remaining_units > 0:
        required_avg_remaining = (target_qpi * total_units - weighted_sum_completed) / remaining_units
        if required_avg_remaining > 100:
            st.warning("Target QPI not mathematically attainable with remaining subjects.")
        elif required_avg_remaining <= 0:
            st.info("Target QPI already secured.")
        else:
            st.info(f"Required average grade for remaining units to reach **{target_qpi:.2f}**: **{required_avg_remaining:.2f}**")
    else:
        st.info("All grades entered. Cumulative QPI already calculated above.")

st.markdown("---")
st.caption("⚠️ This tool is for estimation only and does not replace official evaluation by SBU-COL.")
