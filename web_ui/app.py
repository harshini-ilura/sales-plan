"""
Flask web UI for email campaign management
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sys
from pathlib import Path
from werkzeug.utils import secure_filename
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from database.models import EmailCampaign, EmailTemplate, EmailQueue, SalesLead
from email_service.campaign_manager import CampaignManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change in production


@app.route('/')
def index():
    """Dashboard home"""
    session = get_session()

    try:
        # Get stats
        total_campaigns = session.query(EmailCampaign).filter(
            EmailCampaign.is_deleted == False
        ).count()

        total_leads = session.query(SalesLead).filter(
            SalesLead.is_deleted == False
        ).count()

        total_emails_sent = session.query(EmailQueue).filter(
            EmailQueue.status == 'sent'
        ).count()

        pending_emails = session.query(EmailQueue).filter(
            EmailQueue.status == 'pending'
        ).count()

        # Recent campaigns
        recent_campaigns = session.query(EmailCampaign).filter(
            EmailCampaign.is_deleted == False
        ).order_by(EmailCampaign.created_at.desc()).limit(5).all()

        return render_template(
            'dashboard.html',
            total_campaigns=total_campaigns,
            total_leads=total_leads,
            total_emails_sent=total_emails_sent,
            pending_emails=pending_emails,
            recent_campaigns=recent_campaigns
        )

    finally:
        session.close()


@app.route('/templates')
def templates():
    """List email templates"""
    session = get_session()

    try:
        templates = session.query(EmailTemplate).filter(
            EmailTemplate.is_deleted == False
        ).order_by(EmailTemplate.created_at.desc()).all()

        return render_template('templates.html', templates=templates)

    finally:
        session.close()


@app.route('/templates/create', methods=['GET', 'POST'])
def create_template():
    """Create email template"""
    if request.method == 'POST':
        session = get_session()

        try:
            manager = CampaignManager(session=session)

            template = manager.create_template(
                name=request.form['name'],
                subject=request.form['subject'],
                body_text=request.form['body_text'],
                body_html=request.form.get('body_html'),
                template_type=request.form.get('template_type', 'initial'),
                description=request.form.get('description')
            )

            flash(f'Template "{template.name}" created successfully!', 'success')
            return redirect(url_for('templates'))

        except Exception as e:
            flash(f'Error creating template: {e}', 'danger')
            return redirect(url_for('create_template'))

        finally:
            session.close()

    return render_template('create_template.html', template=None)


@app.route('/templates/<int:template_id>')
def view_template(template_id):
    """View email template details"""
    session = get_session()

    try:
        template = session.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.is_deleted == False
        ).first()

        if not template:
            flash('Template not found', 'danger')
            return redirect(url_for('templates'))

        return render_template('view_template.html', template=template)

    finally:
        session.close()


@app.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
def edit_template(template_id):
    """Edit email template"""
    session = get_session()

    if request.method == 'POST':
        try:
            manager = CampaignManager(session=session)

            template = manager.update_template(
                template_id=template_id,
                name=request.form.get('name'),
                subject=request.form.get('subject'),
                body_text=request.form.get('body_text'),
                body_html=request.form.get('body_html'),
                template_type=request.form.get('template_type'),
                is_active=request.form.get('is_active') == 'on',
                description=request.form.get('description')
            )

            if template:
                flash(f'Template "{template.name}" updated successfully!', 'success')
                return redirect(url_for('view_template', template_id=template_id))
            else:
                flash('Template not found', 'danger')
                return redirect(url_for('templates'))

        except Exception as e:
            flash(f'Error updating template: {e}', 'danger')
            return redirect(url_for('edit_template', template_id=template_id))

        finally:
            session.close()

    # GET: Show edit form
    try:
        template = session.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.is_deleted == False
        ).first()

        if not template:
            flash('Template not found', 'danger')
            return redirect(url_for('templates'))

        return render_template('create_template.html', template=template, is_edit=True)

    finally:
        session.close()


@app.route('/campaigns')
def campaigns():
    """List campaigns"""
    session = get_session()

    try:
        campaigns = session.query(EmailCampaign).filter(
            EmailCampaign.is_deleted == False
        ).order_by(EmailCampaign.created_at.desc()).all()

        return render_template('campaigns.html', campaigns=campaigns)

    finally:
        session.close()


@app.route('/campaigns/create', methods=['GET', 'POST'])
def create_campaign():
    """Create campaign"""
    session = get_session()

    if request.method == 'POST':
        try:
            manager = CampaignManager(session=session)

            # Parse filters
            target_filters = {}
            if request.form.get('filter_country'):
                target_filters['country'] = request.form['filter_country']
            if request.form.get('filter_source'):
                target_filters['source'] = request.form['filter_source']
            if request.form.get('filter_industry'):
                target_filters['industry'] = request.form['filter_industry']

            # Handle attachments
            attachments_data = []
            if 'attachments' in request.files:
                import os
                from werkzeug.utils import secure_filename
                from pathlib import Path
                
                upload_dir = Path('data/uploads')
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                files = request.files.getlist('attachments')
                for file in files:
                    if file.filename:
                        filename = secure_filename(file.filename)
                        filepath = upload_dir / filename
                        file.save(str(filepath))
                        attachments_data.append({
                            'filename': filename,
                            'path': str(filepath),
                            'size': filepath.stat().st_size
                        })

            # Validate sender email (check if it's in allowed list)
            sender_email = request.form['sender_email']
            allowed_emails = ['ilura.ai.tech@gmail.com']  # Add more as needed
            # In production, store this in database/config
            
            campaign = manager.create_campaign(
                name=request.form['name'],
                description=request.form.get('description'),
                template_id=int(request.form['template_id']),
                sender_email=sender_email,
                sender_name=request.form.get('sender_name'),
                reply_to=request.form.get('reply_to'),
                target_filters=target_filters if target_filters else None,
                follow_up_enabled=request.form.get('follow_up_enabled') == 'on',
                follow_up_delay_days=int(request.form.get('follow_up_delay_days', 3)),
                follow_up_template_id=int(request.form['follow_up_template_id'])
                    if request.form.get('follow_up_template_id') else None,
                email_provider=request.form.get('email_provider', 'smtp'),
                smtp_host=request.form.get('smtp_host'),
                smtp_port=int(request.form['smtp_port']) if request.form.get('smtp_port') else None,
                smtp_username=request.form.get('smtp_username'),
                smtp_password=request.form.get('smtp_password'),
                attachments=attachments_data if attachments_data else None,
                send_rate_limit=int(request.form.get('send_rate_limit', 100))
            )

            flash(f'Campaign "{campaign.name}" created successfully!', 'success')
            return redirect(url_for('campaigns'))

        except Exception as e:
            flash(f'Error creating campaign: {e}', 'danger')
            return redirect(url_for('create_campaign'))

        finally:
            session.close()

    # GET: Show form
    try:
        templates = session.query(EmailTemplate).filter(
            EmailTemplate.is_deleted == False,
            EmailTemplate.is_active == True
        ).all()

        return render_template('create_campaign.html', templates=templates)

    finally:
        session.close()


@app.route('/campaigns/<int:campaign_id>')
def campaign_detail(campaign_id):
    """Campaign details and stats"""
    session = get_session()

    try:
        campaign = session.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id,
            EmailCampaign.is_deleted == False
        ).first()

        if not campaign:
            flash('Campaign not found', 'danger')
            return redirect(url_for('campaigns'))

        manager = CampaignManager(session=session)
        stats = manager.get_campaign_stats(campaign_id)

        # Get queue items
        queue_items = session.query(EmailQueue).filter(
            EmailQueue.campaign_id == campaign_id
        ).order_by(EmailQueue.created_at.desc()).limit(50).all()

        # Calculate pending count
        pending_count = session.query(EmailQueue).filter(
            EmailQueue.campaign_id == campaign_id,
            EmailQueue.status == 'pending'
        ).count()

        # Add campaign_id and pending count to stats
        stats['id'] = campaign_id
        stats['emails_pending'] = pending_count

        return render_template(
            'campaign_detail.html',
            stats=stats,
            queue_items=queue_items,
            campaign=campaign
        )

    finally:
        session.close()


@app.route('/campaigns/<int:campaign_id>/queue', methods=['POST'])
def queue_campaign(campaign_id):
    """Queue emails for a campaign"""
    session = get_session()

    try:
        manager = CampaignManager(session=session)

        from_latest_run = request.form.get('from_latest_run') == 'on'
        limit = int(request.form.get('limit', 100))

        if from_latest_run:
            count = manager.queue_from_latest_run(campaign_id, limit=limit)
        else:
            count = manager.queue_campaign(campaign_id)

        flash(f'Queued {count} emails successfully!', 'success')

    except Exception as e:
        flash(f'Error queuing emails: {e}', 'danger')

    finally:
        session.close()

    return redirect(url_for('campaign_detail', campaign_id=campaign_id))


@app.route('/campaigns/<int:campaign_id>/send', methods=['POST'])
def send_campaign_emails(campaign_id):
    """Process and send pending emails for a campaign"""
    session = get_session()

    try:
        from email_service.queue_processor import QueueProcessor
        
        # Get campaign to determine provider
        campaign = session.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id,
            EmailCampaign.is_deleted == False
        ).first()

        if not campaign:
            flash('Campaign not found', 'danger')
            return redirect(url_for('campaigns'))

        # Use campaign's email provider or default to SMTP
        provider_type = campaign.email_provider or 'smtp'
        
        # Create provider with campaign's SMTP settings if available
        from email_service.providers import get_provider, SMTPProvider
        
        if provider_type == 'smtp' and campaign.smtp_host:
            # Use campaign-specific SMTP settings
            provider = SMTPProvider(
                host=campaign.smtp_host,
                port=campaign.smtp_port or 587,
                username=campaign.smtp_username or campaign.sender_email,
                password=campaign.smtp_password
            )
        else:
            # Use default provider
            provider = get_provider(provider_type)
        
        # Create processor with custom provider
        processor = QueueProcessor(
            provider_type=provider_type,
            batch_size=int(request.form.get('batch_size', 10)),
            rate_limit=campaign.send_rate_limit or 100,
            session=session
        )
        # Override provider with campaign-specific one
        processor.provider = provider

        # Process pending emails for this campaign only
        pending_emails = session.query(EmailQueue).filter(
            EmailQueue.campaign_id == campaign_id,
            EmailQueue.status == 'pending',
            EmailQueue.scheduled_at <= datetime.utcnow(),
            EmailQueue.is_deleted == False
        ).order_by(EmailQueue.scheduled_at).limit(int(request.form.get('batch_size', 10))).all()

        sent_count = 0
        failed_count = 0

        for email in pending_emails:
            if processor.send_email(email):
                sent_count += 1
            else:
                failed_count += 1

        processor.close()

        if sent_count > 0:
            flash(f'Successfully sent {sent_count} emails!', 'success')
        if failed_count > 0:
            flash(f'{failed_count} emails failed to send. Check logs for details.', 'warning')
        if sent_count == 0 and failed_count == 0:
            flash('No pending emails to send.', 'info')

    except Exception as e:
        flash(f'Error sending emails: {e}', 'danger')
        import traceback
        traceback.print_exc()

    finally:
        session.close()

    return redirect(url_for('campaign_detail', campaign_id=campaign_id))


@app.route('/leads')
def leads():
    """List leads"""
    session = get_session()

    try:
        page = int(request.args.get('page', 1))
        per_page = 50

        query = session.query(SalesLead).filter(
            SalesLead.is_deleted == False
        ).order_by(SalesLead.created_at.desc())

        total = query.count()
        leads = query.offset((page - 1) * per_page).limit(per_page).all()

        return render_template(
            'leads.html',
            leads=leads,
            page=page,
            per_page=per_page,
            total=total
        )

    finally:
        session.close()


@app.route('/leads/import', methods=['GET', 'POST'])
def import_leads():
    """Import leads from CSV file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('import_leads'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('import_leads'))
        
        if not file.filename.lower().endswith(('.csv', '.txt')):
            flash('Please upload a CSV file', 'danger')
            return redirect(url_for('import_leads'))
        
        try:
            # Save uploaded file
            upload_dir = Path('data/uploads')
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            filename = secure_filename(file.filename)
            filepath = upload_dir / filename
            file.save(str(filepath))
            
            # Import leads
            from scripts.import_csv_leads import import_csv_to_database
            import logging
            
            # Set up logging to capture errors
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            
            source_name = request.form.get('source_name', 'CSV Import')
            skip_duplicates = request.form.get('skip_duplicates') == 'on'
            
            logger.info(f"Starting CSV import: file={filepath}, source={source_name}, skip_duplicates={skip_duplicates}")
            
            stats = import_csv_to_database(
                filepath=str(filepath),
                source_name=source_name,
                skip_duplicates=skip_duplicates
            )
            
            logger.info(f"Import completed: {stats}")
            
            if stats['errors'] > 0:
                flash(f'Imported {stats["imported"]} leads, but {stats["errors"]} errors occurred. '
                      f'({stats["skipped"]} skipped). Check server logs for details.', 'warning')
            elif stats['imported'] == 0 and stats['total'] > 0:
                flash(f'No leads imported. {stats["skipped"]} skipped, {stats["errors"]} errors. '
                      f'Please check your CSV format and ensure it has an "email" column.', 'danger')
            else:
                flash(f'Successfully imported {stats["imported"]} leads! '
                      f'({stats["skipped"]} skipped, {stats["errors"]} errors)', 'success')
            
            # Clean up uploaded file
            if filepath.exists():
                filepath.unlink()
            
            return redirect(url_for('leads'))
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Import error: {error_msg}\n{error_details}")
            flash(f'Error importing leads: {error_msg}. Check server logs for details.', 'danger')
            return redirect(url_for('import_leads'))
    
    # GET: Show import form
    return render_template('import_leads.html')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))  # Default to 8080 to avoid macOS AirPlay conflict
    app.run(debug=True, host='0.0.0.0', port=port)
