import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_transaction_data
from utils.financial_analyzer import calculate_summary

st.set_page_config(page_title="Financial Coach", layout="wide")
st.title("💰 Personalized Financial Coach")

uploaded_file = st.file_uploader("Upload your transaction CSV", type=["csv"])

if uploaded_file:
    df = load_transaction_data(uploaded_file)

    st.subheader("📊 Transactions Preview")
    st.dataframe(df)

    summary = calculate_summary(df)

    st.subheader("💡 Financial Summary")
    for key, value in summary.items():
        st.metric(label=key, value=f"₹{value:,.2f}" if 'Rate' not in key else f"{value}%")

    st.subheader("🎯 Set Your Priorities")

    if "category" in df.columns:
        unique_categories = df["category"].dropna().unique().tolist()
    else:
        unique_categories = []
        st.warning("No 'category' column found in your CSV. Please make sure your data includes a 'category' column.")

    priorities = st.multiselect(
        "What do you want to prioritize spending on?",
        options=unique_categories,
        default=[]
    )

    if priorities:
        st.subheader("📈 Suggested Budget Adjustments")

        # Step 1: Group actual spending per category
        expense_df = df[df["amount"] < 0]
        actual_spending = expense_df.groupby("category")["amount"].sum().abs()

        # Step 2: Apply weights
        adjusted_budget = {}
        priority_weight = 1.2
        non_priority_weight = 0.8
        for cat, amount in actual_spending.items():
            if cat in priorities:
                adjusted_amount = amount * priority_weight
            else:
                adjusted_amount = amount * non_priority_weight
            adjusted_budget[cat] = round(adjusted_amount, 2)

        # Step 3: Calculate total adjusted expenses
        total_income = df[df["amount"] > 0]["amount"].sum()
        total_adjusted_expense = sum(adjusted_budget.values())
        recommended_savings = round(max(0, total_income - total_adjusted_expense), 2)

        # Step 4: Create budget table
        budget_data = pd.DataFrame(list(adjusted_budget.items()), columns=["Category", "Optimized Budget (₹)"])
        budget_data["Actual Spending (₹)"] = budget_data["Category"].map(actual_spending)
        budget_data["Overspent (₹)"] = budget_data["Actual Spending (₹)"] - budget_data["Optimized Budget (₹)"]
        budget_data["Overspent (₹)"] = budget_data["Overspent (₹)"].apply(lambda x: x if x > 0 else 0)

        savings_row = pd.DataFrame([{
            "Category": "Recommended Savings",
            "Optimized Budget (₹)": recommended_savings,
            "Actual Spending (₹)": 0,
            "Overspent (₹)": 0
        }])

        final_budget_df = pd.concat([budget_data, savings_row], ignore_index=True)
        st.write("Here is your optimized monthly budget:")
        st.dataframe(final_budget_df)

        st.metric(
            label="💰 Recommended Savings Budget",
            value=f"₹{recommended_savings:,.2f}"
        )

        # ✅ Pie chart
        st.subheader("📊 Budget Allocation Pie Chart")
        fig = px.pie(
            final_budget_df,
            names="Category",
            values="Optimized Budget (₹)",
            title="Your Optimized Budget Breakdown",
            hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # 🔍 Smart Insight: Overspending warnings
        overspending_alerts = budget_data[budget_data["Overspent (₹)"] > 0]
        if not overspending_alerts.empty:
            st.subheader("💡 Overspending Insights")
            for _, row in overspending_alerts.iterrows():
                st.warning(
                    f"⚠️ You are overspending on **{row['Category']}** by ₹{row['Overspent (₹)']:,.2f}. "
                    f"Try cutting back to stay within your optimized budget!"
                )
        else:
            st.success("✅ You're staying within your optimized budget in all categories. Great job!")

else:
    st.info("Upload a CSV file to get started.")
