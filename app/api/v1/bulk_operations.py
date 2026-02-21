# Eukexpress\backend\app\api\v1\bulk_operations.py
"""
Bulk Operations Endpoints
Mass email campaigns and bulk actions
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
from datetime import datetime
import uuid

from app.database import get_db
from app.models import Shipment, BulkEmailCampaign, Admin
from app.schemas.email import BulkEmailCampaign as BulkEmailSchema, CampaignResponse
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service, email_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/email", response_model=CampaignResponse)
async def send_bulk_email(
    campaign: BulkEmailSchema,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Send bulk email to filtered shipments"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get admin
    admin = db.query(Admin).filter(Admin.username == payload.get("sub")).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    # Build query based on filter
    query = db.query(Shipment)
    
    if campaign.filter == "customs_bond":
        query = query.filter(Shipment.customs_bond_active == True)
    elif campaign.filter == "delayed":
        query = query.filter(Shipment.delay_active == True)
    elif campaign.filter == "international":
        query = query.filter(Shipment.is_international == True)
    elif campaign.filter == "active":
        query = query.filter(Shipment.current_status.notin_(['DELIVERED', 'RETURN_TO_SENDER']))
    # "all" gets all shipments
    
    shipments = query.all()
    recipient_count = len(shipments)
    
    if recipient_count == 0:
        raise HTTPException(status_code=404, detail="No shipments match the filter criteria")
    
    # Create campaign record
    campaign_id = uuid.uuid4()
    campaign_record = BulkEmailCampaign(
        id=campaign_id,
        campaign_name=f"Bulk Email - {campaign.filter} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        recipient_filter=campaign.filter,
        subject=campaign.subject,
        message=campaign.message,
        recipient_count=recipient_count,
        sent_by=admin.id,
        created_at=datetime.utcnow()
    )
    db.add(campaign_record)
    db.commit()
    
    # Send emails in background
    background_tasks.add_task(
        process_bulk_email,
        campaign_id=campaign_id,
        shipments=shipments,
        subject=campaign.subject,
        message=campaign.message,
        include_tracking_links=campaign.include_tracking_links,
        db_session_factory=db.bind
    )
    
    logger.info(f"Bulk email campaign {campaign_id} created for {recipient_count} recipients")
    
    return CampaignResponse(
        success=True,
        campaign_id=str(campaign_id),
        recipient_count=recipient_count,
        estimated_completion=datetime.utcnow()
    )

async def process_bulk_email(campaign_id, shipments, subject, message, include_tracking_links, db_session_factory):
    """Process bulk email in background"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_session_factory)
    db = Session()
    
    try:
        for shipment in shipments:
            tracking_link = f"{settings.APP_URL}/track?number={shipment.tracking_number}" if include_tracking_links else None
            
            # Render bulk message template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='UTF-8'>
                <title>{subject}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #003366; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                    .tracking-link {{ background: #003366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class='container'>
                    <div class='header'>
                        <h1>EukExpress Global Logistics</h1>
                    </div>
                    <div class='content'>
                        <h2>Important Update Regarding Your Shipment {shipment.tracking_number}</h2>
                        <p>Dear {shipment.recipient_name},</p>
                        <div style="background: white; padding: 15px; border-left: 4px solid #003366; margin: 20px 0;">
                            {message}
                        </div>
                        {f'<p><a href="{tracking_link}" class="tracking-link">Track Your Shipment</a></p>' if tracking_link else ''}
                    </div>
                    <div class='footer'>
                        <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
                        <p>This is an automated message from a bulk campaign.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send to recipient
            await email_service.send_email(
                to_email=shipment.recipient_email,
                subject=subject,
                html_content=html_content,
                shipment_id=shipment.id,
                recipient_type="recipient",
                email_type="bulk_campaign"
            )
            
            # Also send to sender if different
            if shipment.sender_email != shipment.recipient_email:
                sender_html = html_content.replace(
                    f"Dear {shipment.recipient_name},",
                    f"Dear {shipment.sender_name},"
                )
                await email_service.send_email(
                    to_email=shipment.sender_email,
                    subject=subject,
                    html_content=sender_html,
                    shipment_id=shipment.id,
                    recipient_type="sender",
                    email_type="bulk_campaign"
                )
        
        # Update campaign status
        campaign = db.query(BulkEmailCampaign).filter(BulkEmailCampaign.id == campaign_id).first()
        if campaign:
            campaign.status = "COMPLETED"
            campaign.completed_at = datetime.utcnow()
            db.commit()
            
        logger.info(f"Bulk email campaign {campaign_id} completed")
        
    except Exception as e:
        logger.error(f"Bulk email campaign {campaign_id} failed: {e}")
        
        # Update campaign status
        campaign = db.query(BulkEmailCampaign).filter(BulkEmailCampaign.id == campaign_id).first()
        if campaign:
            campaign.status = "FAILED"
            campaign.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/campaigns")
async def get_campaigns(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get bulk email campaign history"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    campaigns = db.query(BulkEmailCampaign)\
        .order_by(BulkEmailCampaign.created_at.desc())\
        .limit(50)\
        .all()
    
    result = []
    for campaign in campaigns:
        result.append({
            "campaign_id": str(campaign.id),
            "name": campaign.campaign_name,
            "filter": campaign.recipient_filter,
            "recipient_count": campaign.recipient_count,
            "sent_at": campaign.created_at.isoformat(),
            "status": getattr(campaign, 'status', 'COMPLETED')
        })
    
    return result