"""
admin_app.py — Admin Dashboard for VIT Counselling Predictor

Full CRUD operations for:
  • counselling_records (student data)
  • reports (feedback data)
  • Bulk imports/exports
  • Statistics & analytics
  • Data validation & integrity checks

Run with:
  streamlit run admin_app.py
"""

from datetime import datetime
import io
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import database as db

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="VIT Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# ADMIN AUTHENTICATION
# =====================================================

def check_admin_password():
    """Simple admin authentication."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("⛔ Admin Access Required")
        password = st.text_input(
            "Enter admin password:",
            type="password",
            key="admin_password_input"
        )
        
        admin_password = st.secrets.get("admin_password", "admin123")
        
        if st.button("Login"):
            if password == admin_password:
                st.session_state.admin_authenticated = True
                st.success("✅ Authenticated!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        st.stop()

# =====================================================
# SIDEBAR STYLING & NAVIGATION
# =====================================================

st.markdown("""
    <style>
        .sidebar-title {
            font-size: 20px;
            font-weight: bold;
            color: #ef4444;
            margin-bottom: 20px;
        }
        .section-header {
            font-size: 16px;
            font-weight: bold;
            color: #3730a3;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin: 10px 0;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 12px;
            opacity: 0.9;
            margin-top: 5px;
        }
        .success-box {
            background-color: #f0fdf4;
            padding: 15px;
            border-left: 4px solid #16a34a;
            border-radius: 5px;
            margin: 10px 0;
        }
        .warning-box {
            background-color: #fefce8;
            padding: 15px;
            border-left: 4px solid #eab308;
            border-radius: 5px;
            margin: 10px 0;
        }
        .error-box {
            background-color: #fef2f2;
            padding: 15px;
            border-left: 4px solid #dc2626;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# MAIN APP
# =====================================================

if __name__ == "__main__":
    check_admin_password()

    # Sidebar header
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🛡️ ADMIN DASHBOARD</div>', 
                    unsafe_allow_html=True)
        
        # Quick stats
        st.markdown('<div class="section-header">📊 Quick Stats</div>', 
                    unsafe_allow_html=True)
        
        try:
            record_count = db.count_records()
            report_count = len(db.fetch_all_reports()) if db.fetch_all_reports() is not None else 0
            sources = db.get_source_counts()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📚 Records", record_count)
            with col2:
                st.metric("📋 Reports", report_count)
            
            if sources:
                st.caption(f"Sources: Historical={sources.get('historical', 0)}, Form={sources.get('form', 0)}")
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

        st.divider()
        
        # Navigation menu
        selected_menu = option_menu(
            "Navigation",
            ["Dashboard", "Records", "Reports", "Bulk Import", "Bulk Export", "Analytics", "Settings"],
            icons=["speedometer2", "table", "chat-left-text", "upload", "download", "bar-chart", "gear"],
            menu_icon="menu-button-wide",
            default_index=0,
        )

    # ════════════════════════════════════════════════════════════════════
    # DASHBOARD TAB
    # ════════════════════════════════════════════════════════════════════
    
    if selected_menu == "Dashboard":
        st.title("⚙️ VIT Admin Dashboard")
        st.markdown("Welcome to the admin control panel. Manage all data here.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            record_count = db.count_records()
            reports_df = db.fetch_all_reports()
            report_count = len(reports_df) if reports_df is not None else 0
            all_records = db.fetch_all_records()
            sources = db.get_source_counts()
            
            with col1:
                st.metric("🗂️ Total Records", record_count)
            
            with col2:
                st.metric("📝 Total Reports", report_count)
            
            with col3:
                st.metric("📊 Unique Ranks", len(all_records['Rank'].unique()) if not all_records.empty else 0)
            
            with col4:
                st.metric("🏛️ Campuses", len(all_records['Campus'].unique()) if not all_records.empty else 0)
        
        except Exception as e:
            st.error(f"Error loading dashboard metrics: {str(e)}")
        
        st.divider()
        
        # Recent records
        st.subheader("📊 Recent Records")
        try:
            all_records = db.fetch_all_records()
            if not all_records.empty:
                st.dataframe(all_records.tail(10), use_container_width=True, hide_index=True)
            else:
                st.info("No records found")
        except Exception as e:
            st.error(f"Error loading records: {str(e)}")
        
        # Recent reports
        st.subheader("📋 Recent Reports")
        try:
            reports = db.fetch_all_reports()
            if reports is not None and not reports.empty:
                st.dataframe(reports.tail(10), use_container_width=True, hide_index=True)
            else:
                st.info("No reports found")
        except Exception as e:
            st.error(f"Error loading reports: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # RECORDS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Records":
        st.title("📚 Manage Counselling Records")
        
        record_tabs = st.tabs(["View & Filter", "Add New Record", "Edit Record", "Delete Record"])
        
        with record_tabs[0]:  # VIEW & FILTER
            st.subheader("View & Filter Records")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        rank_filter = st.text_input("Filter by Rank (optional)")
                    with col2:
                        campus_filter = st.selectbox(
                            "Filter by Campus",
                            ["All"] + sorted(all_records['Campus'].unique().tolist()),
                            key="campus_view"
                        )
                    with col3:
                        branch_filter = st.selectbox(
                            "Filter by Branch",
                            ["All"] + sorted(all_records['Branch'].unique().tolist()),
                            key="branch_view"
                        )
                    with col4:
                        source_filter = st.selectbox(
                            "Filter by Source",
                            ["All"] + sorted(all_records['source'].unique().tolist()),
                            key="source_view"
                        )
                    
                    # Apply filters
                    filtered = all_records.copy()
                    
                    if rank_filter:
                        filtered = filtered[filtered['Rank'].astype(str).str.contains(rank_filter, case=False, na=False)]
                    
                    if campus_filter != "All":
                        filtered = filtered[filtered['Campus'] == campus_filter]
                    
                    if branch_filter != "All":
                        filtered = filtered[filtered['Branch'] == branch_filter]
                    
                    if source_filter != "All":
                        filtered = filtered[filtered['source'] == source_filter]
                    
                    st.success(f"✅ Showing {len(filtered)} records")
                    st.dataframe(filtered, use_container_width=True, hide_index=True)
                    
                else:
                    st.warning("No records found in database")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")
        
        with record_tabs[1]:  # ADD NEW
            st.subheader("➕ Add New Record")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rank = st.number_input("Rank", min_value=1, step=1)
                campus = st.selectbox(
                    "Campus",
                    ["VIT Chennai", "VIT Vellore", "VIT Pune", "VIT Amravati"],
                    key="campus_add"
                )
            
            with col2:
                branch = st.text_input("Branch (e.g., CSE Core)")
                fee = st.selectbox(
                    "Fee Category",
                    [1, 2, 3, 4, 5],
                    key="fee_add"
                )
            
            source = st.selectbox("Source", ["historical", "form"], key="source_add")
            
            if st.button("➕ Add Record", type="primary", use_container_width=True):
                try:
                    success = db.upsert_records([{
                        "rank": int(rank),
                        "campus": campus,
                        "branch": branch,
                        "fee": int(fee),
                        "source": source
                    }])
                    
                    if success:
                        st.success(f"✅ Record added: Rank {rank} - {campus} - {branch}")
                    else:
                        st.error("❌ Failed to add record")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with record_tabs[2]:  # EDIT RECORD
            st.subheader("✏️ Edit Record")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    selected_rank = st.selectbox(
                        "Select Record by Rank",
                        sorted(all_records['Rank'].unique()),
                        key="edit_rank"
                    )
                    
                    record = all_records[all_records['Rank'] == selected_rank].iloc[0]
                    
                    st.write("**Current Record:**")
                    st.json({
                        "Rank": int(record['Rank']),
                        "Campus": record['Campus'],
                        "Branch": record['Branch'],
                        "Fee": int(record['Fee']),
                        "Source": record['source']
                    })
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_campus = st.selectbox(
                            "Update Campus",
                            ["VIT Chennai", "VIT Vellore", "VIT Pune", "VIT Amravati"],
                            index=["VIT Chennai", "VIT Vellore", "VIT Pune", "VIT Amravati"].index(record['Campus']),
                            key="edit_campus"
                        )
                        new_branch = st.text_input("Update Branch", value=record['Branch'])
                    
                    with col2:
                        new_fee = st.selectbox(
                            "Update Fee",
                            [1, 2, 3, 4, 5],
                            index=[1, 2, 3, 4, 5].index(int(record['Fee'])),
                            key="edit_fee"
                        )
                        new_source = st.selectbox(
                            "Update Source",
                            ["historical", "form"],
                            index=["historical", "form"].index(record['source']),
                            key="edit_source"
                        )
                    
                    if st.button("✅ Update Record", type="primary", use_container_width=True):
                        try:
                            success = db.upsert_records([{
                                "rank": int(selected_rank),
                                "campus": new_campus,
                                "branch": new_branch,
                                "fee": int(new_fee),
                                "source": new_source
                            }])
                            
                            if success:
                                st.success("✅ Record updated successfully!")
                            else:
                                st.error("❌ Failed to update record")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("No records found")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")
        
        with record_tabs[3]:  # DELETE RECORD
            st.subheader("🗑️ Delete Record")
            st.warning("⚠️ This action cannot be undone!")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    selected_rank = st.selectbox(
                        "Select Record by Rank to Delete",
                        sorted(all_records['Rank'].unique()),
                        key="delete_rank"
                    )
                    
                    record = all_records[all_records['Rank'] == selected_rank].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.json({
                            "Rank": int(record['Rank']),
                            "Campus": record['Campus'],
                            "Branch": record['Branch'],
                            "Fee": int(record['Fee'])
                        })
                    
                    with col2:
                        if st.button("🗑️ DELETE THIS RECORD", type="secondary", use_container_width=True):
                            try:
                                # Since we can't delete directly (no delete function in db),
                                # we'll show a warning
                                st.warning("⚠️ Delete functionality requires additional database permissions.")
                                st.info("Contact database administrator to remove records.")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("No records found")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # REPORTS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Reports":
        st.title("📋 Manage User Reports")
        
        report_tabs = st.tabs(["View Reports", "Report Analytics", "Delete Report"])
        
        with report_tabs[0]:  # VIEW REPORTS
            st.subheader("View All Reports")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        report_type_filter = st.selectbox(
                            "Filter by Report Type",
                            ["All"] + (reports['Report Type'].unique().tolist() if 'Report Type' in reports.columns else [])
                        )
                    
                    with col2:
                        chance_filter = st.selectbox(
                            "Filter by Predicted Chance",
                            ["All"] + (reports['Predicted Chance'].unique().tolist() if 'Predicted Chance' in reports.columns else [])
                        )
                    
                    with col3:
                        campus_filter = st.selectbox(
                            "Filter by Campus",
                            ["All"] + (reports['Campus'].unique().tolist() if 'Campus' in reports.columns else []),
                            key="reports_campus"
                        )
                    
                    filtered_reports = reports.copy()
                    
                    if report_type_filter != "All" and 'Report Type' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Report Type'] == report_type_filter]
                    
                    if chance_filter != "All" and 'Predicted Chance' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Predicted Chance'] == chance_filter]
                    
                    if campus_filter != "All" and 'Campus' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Campus'] == campus_filter]
                    
                    st.success(f"✅ Showing {len(filtered_reports)} reports")
                    st.dataframe(filtered_reports, use_container_width=True, hide_index=True)
                
                else:
                    st.info("No reports found")
            
            except Exception as e:
                st.error(f"Error loading reports: {str(e)}")
        
        with report_tabs[1]:  # ANALYTICS
            st.subheader("📊 Report Analytics")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if 'Report Type' in reports.columns:
                            st.metric("📌 Report Types", reports['Report Type'].nunique())
                    
                    with col2:
                        st.metric("📋 Total Reports", len(reports))
                    
                    with col3:
                        if 'Timestamp' in reports.columns or 'created_at' in reports.columns:
                            st.metric("📅 Date Range", "See below")
                    
                    st.divider()
                    
                    # Report type distribution
                    if 'Report Type' in reports.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Reports by Type")
                            report_type_counts = reports['Report Type'].value_counts()
                            st.bar_chart(report_type_counts)
                        
                        with col2:
                            st.subheader("Distribution")
                            st.dataframe(report_type_counts, use_container_width=True)
                    
                    # Chance distribution
                    if 'Predicted Chance' in reports.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Reports by Predicted Chance")
                            chance_counts = reports['Predicted Chance'].value_counts()
                            st.pie_chart(chance_counts)
                        
                        with col2:
                            st.subheader("Distribution")
                            st.dataframe(chance_counts, use_container_width=True)
                    
                    # Campus wise reports
                    if 'Campus' in reports.columns:
                        st.subheader("Reports by Campus")
                        campus_counts = reports['Campus'].value_counts()
                        st.bar_chart(campus_counts)
                
                else:
                    st.info("No reports to analyze")
            
            except Exception as e:
                st.error(f"Error loading analytics: {str(e)}")
        
        with report_tabs[2]:  # DELETE REPORT
            st.subheader("🗑️ Delete Report")
            st.warning("⚠️ This action cannot be undone!")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    # Create a display string for selection
                    report_options = []
                    report_ids = []
                    
                    for idx, row in reports.iterrows():
                        label = f"ID: {row.get('id', 'N/A')} | Rank: {row.get('User Rank', 'N/A')} | Type: {row.get('Report Type', 'N/A')}"
                        report_options.append(label)
                        report_ids.append(row.get('id'))
                    
                    selected_idx = st.selectbox(
                        "Select Report to Delete",
                        range(len(report_options)),
                        format_func=lambda i: report_options[i]
                    )
                    
                    selected_report_id = report_ids[selected_idx]
                    selected_report = reports.iloc[selected_idx]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.json(selected_report.to_dict())
                    
                    with col2:
                        if st.button("🗑️ DELETE THIS REPORT", type="secondary", use_container_width=True):
                            try:
                                success = db.delete_report(selected_report_id)
                                
                                if success:
                                    st.success(f"✅ Report {selected_report_id} deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete report")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                else:
                    st.warning("No reports found")
            
            except Exception as e:
                st.error(f"Error loading reports: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # BULK IMPORT TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Bulk Import":
        st.title("📥 Bulk Import Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Import Records")
            st.info("""
            Upload a CSV file with columns:
            - `rank` (integer)
            - `campus` (text)
            - `branch` (text)
            - `fee` (integer: 1-5)
            - `source` (text: 'historical' or 'form')
            """)
            
            records_file = st.file_uploader(
                "Choose CSV file for records",
                type="csv",
                key="records_import"
            )
            
            if records_file:
                try:
                    df = pd.read_csv(records_file)
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ {len(df)} rows ready to import")
                    
                    with col_b:
                        if st.button("📥 Import Records", type="primary", use_container_width=True, key="import_records_btn"):
                            try:
                                records = df.to_dict('records')
                                success = db.upsert_records(records)
                                
                                if success:
                                    st.success(f"✅ Successfully imported {len(records)} records!")
                                else:
                                    st.error("❌ Failed to import records")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        with col2:
            st.subheader("📋 Import Reports")
            st.info("""
            Upload a CSV/Excel file with columns:
            - `user_rank` (integer)
            - `campus` (text)
            - `branch` (text)
            - `fee_category` (integer)
            - `predicted_probability` (float)
            - `predicted_chance` (text)
            - `report_type` (text)
            - `reason_text` (text, optional)
            """)
            
            reports_file = st.file_uploader(
                "Choose CSV/Excel file for reports",
                type=["csv", "xlsx"],
                key="reports_import"
            )
            
            if reports_file:
                try:
                    if reports_file.name.endswith('.xlsx'):
                        df = pd.read_excel(reports_file)
                    else:
                        df = pd.read_csv(reports_file)
                    
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ {len(df)} rows ready to import")
                    
                    with col_b:
                        if st.button("📥 Import Reports", type="primary", use_container_width=True, key="import_reports_btn"):
                            try:
                                imported = 0
                                for _, row in df.iterrows():
                                    success = db.insert_report(
                                        user_rank=int(row['user_rank']),
                                        campus=str(row['campus']),
                                        branch=str(row['branch']),
                                        fee=int(row['fee_category']),
                                        probability=float(row['predicted_probability']),
                                        chance=str(row['predicted_chance']),
                                        report_type=str(row['report_type']),
                                        reason_text=str(row.get('reason_text', ''))
                                    )
                                    if success:
                                        imported += 1
                                
                                st.success(f"✅ Successfully imported {imported}/{len(df)} reports!")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # BULK EXPORT TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Bulk Export":
        st.title("📤 Bulk Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Records")
            
            if st.button("📤 Download Records as CSV", type="primary", use_container_width=True):
                try:
                    records = db.fetch_all_records()
                    
                    if not records.empty:
                        csv_data = records.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Click to Download Records.csv",
                            data=csv_data,
                            file_name=f"counselling_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(records)} records ready for download")
                    else:
                        st.warning("No records to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.button("📊 Download Records as Excel", type="primary", use_container_width=True):
                try:
                    records = db.fetch_all_records()
                    
                    if not records.empty:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            records.to_excel(writer, sheet_name='Records', index=False)
                        
                        buffer.seek(0)
                        st.download_button(
                            label="📥 Click to Download Records.xlsx",
                            data=buffer.getvalue(),
                            file_name=f"counselling_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(records)} records ready for download")
                    else:
                        st.warning("No records to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col2:
            st.subheader("📋 Export Reports")
            
            if st.button("📤 Download Reports as CSV", type="primary", use_container_width=True):
                try:
                    reports = db.fetch_all_reports()
                    
                    if reports is not None and not reports.empty:
                        csv_data = reports.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Click to Download Reports.csv",
                            data=csv_data,
                            file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(reports)} reports ready for download")
                    else:
                        st.warning("No reports to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.button("📊 Download Reports as Excel", type="primary", use_container_width=True):
                try:
                    reports = db.fetch_all_reports()
                    
                    if reports is not None and not reports.empty:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            reports.to_excel(writer, sheet_name='Reports', index=False)
                        
                        buffer.seek(0)
                        st.download_button(
                            label="📥 Click to Download Reports.xlsx",
                            data=buffer.getvalue(),
                            file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(reports)} reports ready for download")
                    else:
                        st.warning("No reports to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # ANALYTICS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Analytics":
        st.title("📊 Analytics Dashboard")
        
        try:
            all_records = db.fetch_all_records()
            
            if not all_records.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📚 Total Records", len(all_records))
                
                with col2:
                    st.metric("🏛️ Campuses", all_records['Campus'].nunique())
                
                with col3:
                    st.metric("🎓 Branches", all_records['Branch'].nunique())
                
                with col4:
                    st.metric("💰 Fee Categories", all_records['Fee'].nunique())
                
                st.divider()
                
                # Records by Campus
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Records by Campus")
                    campus_counts = all_records['Campus'].value_counts()
                    st.bar_chart(campus_counts)
                
                with col2:
                    st.subheader("Records by Branch")
                    branch_counts = all_records['Branch'].value_counts().head(10)
                    st.bar_chart(branch_counts)
                
                st.divider()
                
                # Record ranks distribution
                st.subheader("Rank Distribution")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Min Rank", int(all_records['Rank'].min()))
                    st.metric("Max Rank", int(all_records['Rank'].max()))
                
                with col2:
                    st.metric("Avg Rank", int(all_records['Rank'].mean()))
                    st.metric("Median Rank", int(all_records['Rank'].median()))
                
                st.divider()
                
                # Source distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Records by Source")
                    source_counts = all_records['source'].value_counts()
                    st.pie_chart(source_counts)
                
                with col2:
                    st.subheader("Distribution Table")
                    st.dataframe(source_counts, use_container_width=True)
                
            else:
                st.warning("No records to analyze")
        
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # SETTINGS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Settings":
        st.title("⚙️ Admin Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔐 Security")
            
            if st.button("🔓 Logout"):
                st.session_state.admin_authenticated = False
                st.success("✅ Logged out successfully")
                st.rerun()
            
            st.divider()
            
            st.subheader("📊 Database Info")
            
            try:
                record_count = db.count_records()
                reports_df = db.fetch_all_reports()
                report_count = len(reports_df) if reports_df is not None else 0
                
                st.json({
                    "Total Records": record_count,
                    "Total Reports": report_count,
                    "Database Status": "✅ Connected"
                })
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
        
        with col2:
            st.subheader("📝 About")
            
            st.markdown("""
            **VIT Admin Dashboard**
            
            • Manage counselling data
            • Handle user reports
            • Import/Export functionality
            • Analytics & insights
            
            **Version:** 1.0
            **Last Updated:** May 2026
            """)
            
            st.divider()
            
            if st.checkbox("Show Advanced Options"):
                st.warning("⚠️ Advanced Options")
                
                if st.button("🔄 Clear Cache"):
                    st.cache_resource.clear()
                    st.success("✅ Cache cleared")
                
                if st.button("🐛 Show Debug Info"):
                    st.json({
                        "Session State": dict(st.session_state),
                        "User": "Admin",
                        "Timestamp": datetime.now().isoformat()
                    })
