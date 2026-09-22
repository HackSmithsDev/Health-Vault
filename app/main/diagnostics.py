from flask import render_template, abort, request, session
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from app.extensions import db

from app.models import (
    DiagnosticUnit, Subject, ClinicalSession, DiagnosticReport
)
from . import main_bp

@main_bp.route('/diagnostic/unit/<unit_id>')
@login_required
def clinical_unit(unit_id):
    if session.get('user_role') == 'patient':
        abort(403)  # Patients should not access this route
    unit = DiagnosticUnit.query.options(joinedload(DiagnosticUnit.subjects)).get(unit_id)
    if not unit:
        abort(404)
    
    # 1. Aggregate based on subject_id (database column)
    stats_query = db.session.query(
        ClinicalSession.subject_id,
        func.count(ClinicalSession.id).label('total'),
        func.sum(db.case((ClinicalSession.status == 'Flagged', 1), else_=0)).label('flagged')
    ).filter(ClinicalSession.unit_id == unit_id).group_by(ClinicalSession.subject_id).all()

    # 2. Build the stats map using the Subject Object itself to avoid string mismatches
    # We use a nested dict: { "subject_id": { "name": "...", "count": 0 } }
    formatted_stats = {}
    for s in unit.subjects:
        # Initialize every subject in the unit (Ensures 5 subjects show up)
        formatted_stats[s.id] = {
            'name': s.name,
            'count': 0,
            'high_risk': 0
        }

    # 3. Fill in the actual numbers from the database
    for row in stats_query:
        if row.subject_id in formatted_stats:
            formatted_stats[row.subject_id]['count'] = row.total
            formatted_stats[row.subject_id]['high_risk'] = int(row.flagged or 0)
        
    return render_template('clinical_unit.html', 
                           unit_id=unit_id,
                           unit_name=unit.name, 
                           unit_subjects=unit.subjects, # Pass the actual objects
                           stats=formatted_stats)

@main_bp.route('/diagnostic/unit/<unit_id>/subject/<subject_name>')
@login_required
def subject_chapters(unit_id, subject_name):
    if session.get('user_role') == 'patient':
        abort(403)  # Patients should not access this route
    # 1. Get Subject by Name to get the correct ID
    subject = Subject.query.filter_by(unit_id=unit_id, name=subject_name).first_or_404()
    
    # 2. FIX: Filter by subject_id instead of session_name string matching
    records = ClinicalSession.query.filter(
        ClinicalSession.unit_id == unit_id,
        ClinicalSession.subject_id == subject.id  # Precise ID matching
    ).options(joinedload(ClinicalSession.reports)).order_by(ClinicalSession.created_at.desc()).all()
    
    # 3. Calculate stats for the top cards
    stats = {
        'total_cases': len(records),
        'high_risk': sum(1 for r in records if r.status == 'Flagged'),
        'active_monitoring': sum(1 for r in records if r.status == 'Monitoring'),
        'resolved': sum(1 for r in records if r.status == 'Resolved')
    }
    
    return render_template('clinical_unit_data.html', 
                           unit_id=unit_id,
                           unit_name=subject.unit.name, 
                           subject_name=subject.name, 
                           chapters=subject.chapters, # Passing full objects
                           records=records,
                           stats=stats)