from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Response
from typing import List, Optional, Any
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64
import secrets
import string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from ..storage.memory_adapter import db, desc
from ..models import (
    User, SecurityEvent, SecurityEventType, TwoFactorMethod
, Any)
# TwoFactorAuth, UserDevice, SecurityAuditLog models not yet implemented
from ..models import (
    TwoFactorSetup, TwoFactorVerify, TwoFactorResponse, TwoFactorSetupResponse,
    UserDeviceResponse, DeviceTrustUpdate, SecurityAuditLogResponse
)
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError
from ..utils.session_manager import session_manager
from ..utils.security_logger import log_security_event, get_or_create_device
from ..utils.communications import send_2fa_sms, send_2fa_email, verify_code

router = APIRouter()

def generate_backup_codes(count: int = 8) -> List[str]:
    """Generate backup codes"""
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes

def generate_totp_secret() -> str:
    """Generate TOTP secret"""
    return pyotp.random_base32()

def generate_qr_code(user_email: str, secret: str, issuer: str = "BankingApp") -> str:
    """Generate QR code for TOTP setup"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=issuer
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    
    return base64.b64encode(buf.getvalue()).decode()

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    request: Request,
    setup_data: TwoFactorSetup,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Setup two-factor authentication"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Check if method already exists
    existing = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.method == setup_data.method
    ).first()
    
    if existing and existing.is_enabled:
        raise ValidationError(f"2FA method {setup_data.method.value} is already enabled")
    
    # Get user for email
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    # Create or update 2FA method
    if not existing:
        two_factor = TwoFactorAuth(
            user_id=current_user['user_id'],
            method=setup_data.method
        )
        db_session.add(two_factor)
    else:
        two_factor = existing
    
    response_data = {
        "id": two_factor.id if existing else 0,
        "method": setup_data.method,
        "is_enabled": False,
        "is_primary": False,
        "created_at": two_factor.created_at if existing else datetime.utcnow()
    }
    
    # Setup based on method
    if setup_data.method == TwoFactorMethod.AUTHENTICATOR:
        secret = generate_totp_secret()
        two_factor.secret = secret  # In production, encrypt this
        response_data["secret"] = secret
        response_data["qr_code"] = generate_qr_code(user.email, secret)
        
    elif setup_data.method == TwoFactorMethod.SMS:
        if not setup_data.phone_number:
            raise ValidationError("Phone number required for SMS 2FA")
        two_factor.phone_number = setup_data.phone_number
        # Send verification SMS
        await send_2fa_sms(setup_data.phone_number, current_user['user_id'])
        response_data["message"] = "Verification code sent to your phone"
        
    elif setup_data.method == TwoFactorMethod.EMAIL:
        email_to_use = setup_data.email or user.email
        two_factor.email = email_to_use
        # Send verification email
        await send_2fa_email(email_to_use, current_user['user_id'])
        response_data["message"] = "Verification code sent to your email"
        
    elif setup_data.method == TwoFactorMethod.BACKUP_CODES:
        codes = generate_backup_codes()
        two_factor.backup_codes = codes  # In production, hash these
        response_data["backup_codes"] = codes
    
    if not existing:
        db_session.flush()
        response_data["id"] = two_factor.id
    
    db_session.commit()

    return TwoFactorSetupResponse(**response_data)

@router.post("/2fa/verify/{method}")
async def verify_two_factor(
    request: Request,
    method: TwoFactorMethod,
    verify_data: TwoFactorVerify,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Verify and enable two-factor authentication"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Get 2FA method
    two_factor = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.method == method
    ).first()
    
    if not two_factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA method not found"
        )
    
    # Verify based on method
    verified = False
    
    if method == TwoFactorMethod.AUTHENTICATOR:
        totp = pyotp.TOTP(two_factor.secret)
        verified = totp.verify(verify_data.code, valid_window=1)
        
    elif method == TwoFactorMethod.SMS:
        verified, error_msg = verify_code(current_user['user_id'], "sms", verify_data.code)
        if not verified:
            raise ValidationError(error_msg)
            
    elif method == TwoFactorMethod.EMAIL:
        verified, error_msg = verify_code(current_user['user_id'], "email", verify_data.code)
        if not verified:
            raise ValidationError(error_msg)
        
    elif method == TwoFactorMethod.BACKUP_CODES:
        # Check if code exists and hasn't been used
        if verify_data.code in two_factor.backup_codes:
            verified = True
            # Remove used code
            two_factor.backup_codes = [c for c in two_factor.backup_codes if c != verify_data.code]
    
    if not verified:
        log_security_event(
            db_session,
            current_user['user_id'],
            SecurityEventType.TWO_FACTOR_ENABLED,
            request,
            success=False,
            failure_reason="Invalid verification code"
        )
        raise ValidationError("Invalid verification code")
    
    # Enable 2FA
    two_factor.is_enabled = True
    
    # Set as primary if it's the first one
    other_methods = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.id != two_factor.id,
        TwoFactorAuth.is_enabled == True
    ).count()
    
    if other_methods == 0:
        two_factor.is_primary = True
    
    db_session.commit()
    
    # Log success
    log_security_event(
        db_session,
        current_user['user_id'],
        SecurityEventType.TWO_FACTOR_ENABLED,
        request,
        metadata={"method": method.value}
    )
    
    return {"message": f"2FA {method.value} enabled successfully"}

@router.post("/2fa/resend/{method}")
async def resend_verification_code(
    request: Request,
    method: TwoFactorMethod,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Resend verification code for SMS/Email 2FA"""
    if method not in [TwoFactorMethod.SMS, TwoFactorMethod.EMAIL]:
        raise ValidationError("Resend only available for SMS and Email methods")
    
    # Get 2FA method
    two_factor = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.method == method
    ).first()
    
    if not two_factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA method not found"
        )
    
    # Resend code
    if method == TwoFactorMethod.SMS:
        if not two_factor.phone_number:
            raise ValidationError("Phone number not configured")
        success = await send_2fa_sms(two_factor.phone_number, current_user['user_id'])
    else:  # Email
        user = db_session.query(User).filter(User.id == current_user['user_id']).first()
        email = two_factor.email or user.email
        success = await send_2fa_email(email, current_user['user_id'])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )
    
    return {"message": f"Verification code resent via {method.value}"}

@router.get("/2fa", response_model=List[TwoFactorResponse])
async def get_two_factor_methods(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all 2FA methods for current user"""
    methods = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id']
    ).all()
    
    return [TwoFactorResponse.from_orm(m) for m in methods]

@router.delete("/2fa/{method}")
async def disable_two_factor(
    request: Request,
    method: TwoFactorMethod,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Disable a 2FA method"""
    two_factor = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.method == method
    ).first()
    
    if not two_factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA method not found"
        )
    
    # Check if it's the only enabled method
    if two_factor.is_primary:
        other_enabled = db_session.query(TwoFactorAuth).filter(
            TwoFactorAuth.user_id == current_user['user_id'],
            TwoFactorAuth.id != two_factor.id,
            TwoFactorAuth.is_enabled == True
        ).first()
        
        if other_enabled:
            other_enabled.is_primary = True
    
    db_session.delete(two_factor)
    db_session.commit()
    
    # Log the action
    log_security_event(
        db_session,
        current_user['user_id'],
        SecurityEventType.TWO_FACTOR_DISABLED,
        request,
        metadata={"method": method.value}
    )
    
    return {"message": f"2FA {method.value} disabled successfully"}

@router.get("/devices", response_model=List[UserDeviceResponse])
async def get_user_devices(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all devices for current user"""
    query = db_session.query(UserDevice).filter(
        UserDevice.user_id == current_user['user_id']
    )
    
    if not include_inactive:
        query = query.filter(UserDevice.is_active == True)
    
    devices = query.order_by(UserDevice.last_active_at.desc()).all()
    
    return [UserDeviceResponse.from_orm(d) for d in devices]

@router.get("/devices/current", response_model=UserDeviceResponse)
async def get_current_device(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get current device information"""
    device = get_or_create_device(db_session, current_user['user_id'], request)
    return UserDeviceResponse.from_orm(device)

@router.put("/devices/{device_id}/trust", response_model=UserDeviceResponse)
async def update_device_trust(
    device_id: int,
    trust_data: DeviceTrustUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Mark a device as trusted/untrusted"""
    device = db_session.query(UserDevice).filter(
        UserDevice.id == device_id,
        UserDevice.user_id == current_user['user_id']
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device.is_trusted = trust_data.is_trusted
    db_session.commit()
    db_session.refresh(device)
    
    return UserDeviceResponse.from_orm(device)

@router.delete("/devices/{device_id}")
async def remove_device(
    request: Request,
    device_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Remove a device (logout from that device)"""
    device = db_session.query(UserDevice).filter(
        UserDevice.id == device_id,
        UserDevice.user_id == current_user['user_id']
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Don't allow removing current device
    current_device = get_or_create_device(db_session, current_user['user_id'], request)
    if device.id == current_device.id:
        raise ValidationError("Cannot remove current device")
    
    device.is_active = False
    db_session.commit()
    
    return {"message": "Device removed successfully"}

@router.get("/audit-logs", response_model=List[SecurityAuditLogResponse])
async def get_security_audit_logs(
    event_type: Optional[SecurityEventType] = None,
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get security audit logs for current user"""
    since_date = datetime.utcnow() - timedelta(days=days_back)
    
    query = db_session.query(SecurityAuditLog).filter(
        SecurityAuditLog.user_id == current_user['user_id'],
        SecurityAuditLog.created_at >= since_date
    )
    
    if event_type:
        query = query.filter(SecurityAuditLog.event_type == event_type)
    
    logs = query.order_by(SecurityAuditLog.created_at.desc()).limit(limit).all()
    
    results = []
    for log in logs:
        response = SecurityAuditLogResponse.from_orm(log)
        if log.device:
            response.device_name = log.device.device_name
        results.append(response)
    
    return results

@router.get("/audit-logs/summary")
async def get_security_summary(
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get security summary for current user"""
    since_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Count events by type
    event_counts = {}
    for event_type in SecurityEventType:
        count = db_session.query(SecurityAuditLog).filter(
            SecurityAuditLog.user_id == current_user['user_id'],
            SecurityAuditLog.created_at >= since_date,
            SecurityAuditLog.event_type == event_type
        ).count()
        if count > 0:
            event_counts[event_type.value] = count
    
    # Count failed login attempts
    failed_logins = db_session.query(SecurityAuditLog).filter(
        SecurityAuditLog.user_id == current_user['user_id'],
        SecurityAuditLog.created_at >= since_date,
        SecurityAuditLog.event_type == SecurityEventType.LOGIN_FAILED
    ).count()
    
    # Get active devices
    active_devices = db_session.query(UserDevice).filter(
        UserDevice.user_id == current_user['user_id'],
        UserDevice.is_active == True
    ).count()
    
    # Get 2FA status
    two_factor_enabled = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.is_enabled == True
    ).count() > 0
    
    return {
        "event_counts": event_counts,
        "failed_login_attempts": failed_logins,
        "active_devices": active_devices,
        "two_factor_enabled": two_factor_enabled,
        "period_days": days_back
    }

@router.get("/export/report/pdf")
async def export_security_report_pdf(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Export comprehensive security report in PDF format"""
    # Get user data
    user = db_session.query(User).filter(User.id == current_user['user_id']).first()
    
    # Get security events (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    security_events = db_session.query(SecurityEvent).filter(
        SecurityEvent.user_id == current_user['user_id'],
        SecurityEvent.created_at >= thirty_days_ago
    ).order_by(SecurityEvent.created_at.desc()).all()
    
    # Get active sessions/devices
    active_devices = db_session.query(UserDevice).filter(
        UserDevice.user_id == current_user['user_id'],
        UserDevice.is_active == True
    ).order_by(UserDevice.last_active_at.desc()).all()
    
    # Get 2FA methods
    two_factor_methods = db_session.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user['user_id'],
        TwoFactorAuth.is_enabled == True
    ).all()
    
    # Calculate security score
    security_score = 50  # Base score
    if user.password and len(user.password) > 0:
        security_score += 20
    if len(two_factor_methods) > 0:
        security_score += 30
    
    # Count suspicious events
    suspicious_events = [e for e in security_events if e.event_type in [
        SecurityEventType.LOGIN_FAILED,
        SecurityEventType.SUSPICIOUS_ACTIVITY
    ]]
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Title
    story.append(Paragraph("Security Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Paragraph(f"User: {user.username}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Security Score Section
    story.append(Paragraph("Security Overview", heading_style))
    
    score_label = "Excellent" if security_score >= 80 else "Good" if security_score >= 60 else "Fair" if security_score >= 40 else "Poor"
    score_color = colors.green if security_score >= 80 else colors.orange if security_score >= 60 else colors.red
    
    overview_data = [
        ['Security Score:', f'{security_score}/100 ({score_label})'],
        ['Two-Factor Authentication:', 'Enabled' if len(two_factor_methods) > 0 else 'Disabled'],
        ['Active Sessions:', str(len(active_devices))],
        ['Recent Security Events:', str(len(security_events))],
        ['Suspicious Activities (30 days):', str(len(suspicious_events))]
    ]
    
    overview_table = Table(overview_data, colWidths=[3*inch, 3*inch])
    overview_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Security Features
    story.append(Paragraph("Security Features", heading_style))
    
    features_data = [
        ['Feature', 'Status', 'Details'],
        ['Password Protection', 'Enabled', 'Last changed: Unknown'],
        ['Two-Factor Authentication', 
         'Enabled' if len(two_factor_methods) > 0 else 'Disabled',
         ', '.join([m.method.value for m in two_factor_methods]) if two_factor_methods else 'Not configured'],
        ['Biometric Login', 'Not Available', 'Device-specific feature'],
        ['Trusted Devices', f'{len([d for d in active_devices if hasattr(d, "is_trusted") and d.is_trusted])} devices', 'Manage in settings']
    ]
    
    features_table = Table(features_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(features_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Active Sessions
    story.append(Paragraph("Active Sessions", heading_style))
    
    if active_devices:
        session_data = [['Device', 'Location', 'Last Active', 'Status']]
        for device in active_devices[:10]:  # Limit to 10 most recent
            session_data.append([
                device.device_name if hasattr(device, 'device_name') else 'Unknown Device',
                device.location if hasattr(device, 'location') else 'Unknown',
                device.last_active_at.strftime('%m/%d/%Y %I:%M %p') if hasattr(device, 'last_active_at') else 'Unknown',
                'Current' if hasattr(device, 'is_current') and device.is_current else 'Active'
            ])
        
        session_table = Table(session_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(session_table)
    else:
        story.append(Paragraph("No active sessions found.", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Recent Security Events
    story.append(Paragraph("Recent Security Events (Last 30 Days)", heading_style))
    
    if security_events:
        event_data = [['Date/Time', 'Event', 'Location', 'Status']]
        for event in security_events[:15]:  # Limit to 15 most recent
            status_text = 'Success' if event.success else 'Failed'
            if event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY:
                status_text = 'Warning'
            
            event_data.append([
                event.created_at.strftime('%m/%d %I:%M %p'),
                event.event_type.value.replace('_', ' ').title(),
                event.location if hasattr(event, 'location') else 'Unknown',
                status_text
            ])
        
        event_table = Table(event_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1*inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(event_table)
    else:
        story.append(Paragraph("No security events in the last 30 days.", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    story.append(Paragraph("Security Recommendations", heading_style))
    
    recommendations = []
    if len(two_factor_methods) == 0:
        recommendations.append("• Enable Two-Factor Authentication for enhanced account security")
    if security_score < 80:
        recommendations.append("• Review and update your security settings regularly")
    if len(suspicious_events) > 0:
        recommendations.append("• Review suspicious activities and ensure your account hasn't been compromised")
    if len(active_devices) > 5:
        recommendations.append("• Review active sessions and remove any unrecognized devices")
    
    recommendations.extend([
        "• Use strong, unique passwords for your account",
        "• Keep your contact information up to date",
        "• Enable login notifications to monitor account access",
        "• Regularly review your security settings"
    ])
    
    for rec in recommendations:
        story.append(Paragraph(rec, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=security_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        }
    )