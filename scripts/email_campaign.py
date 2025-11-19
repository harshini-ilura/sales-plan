#!/usr/bin/env python3
"""
Email campaign management CLI
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import session_scope
from email_service.campaign_manager import CampaignManager


def create_template(args):
    """Create an email template"""
    with session_scope() as session:
        manager = CampaignManager(session=session)

        template = manager.create_template(
            name=args.name,
            subject=args.subject,
            body_text=args.body_text,
            body_html=args.body_html,
            template_type=args.template_type
        )

        print(f"✓ Template created: ID={template.id}, Name={template.name}")


def create_campaign(args):
    """Create an email campaign"""
    with session_scope() as session:
        manager = CampaignManager(session=session)

        # Parse filters if provided
        target_filters = {}
        if args.country:
            target_filters['country'] = args.country
        if args.source:
            target_filters['source'] = args.source
        if args.industry:
            target_filters['industry'] = args.industry

        campaign = manager.create_campaign(
            name=args.name,
            template_id=args.template_id,
            sender_email=args.sender_email,
            sender_name=args.sender_name,
            description=args.description,
            target_filters=target_filters if target_filters else None,
            follow_up_enabled=args.follow_up,
            follow_up_delay_days=args.follow_up_days,
            follow_up_template_id=args.follow_up_template_id
        )

        print(f"✓ Campaign created: ID={campaign.id}, Name={campaign.name}")


def queue_campaign(args):
    """Queue emails for a campaign"""
    with session_scope() as session:
        manager = CampaignManager(session=session)

        if args.from_latest_run:
            # Queue from latest Apify run
            count = manager.queue_from_latest_run(
                campaign_id=args.campaign_id,
                limit=args.limit
            )
        else:
            # Queue from database based on filters
            count = manager.queue_campaign(
                campaign_id=args.campaign_id
            )

        print(f"✓ Queued {count} emails for campaign {args.campaign_id}")


def schedule_follow_ups(args):
    """Schedule follow-up emails"""
    with session_scope() as session:
        manager = CampaignManager(session=session)

        count = manager.schedule_follow_ups(args.campaign_id)

        print(f"✓ Scheduled {count} follow-up emails")


def show_stats(args):
    """Show campaign statistics"""
    with session_scope() as session:
        manager = CampaignManager(session=session)

        stats = manager.get_campaign_stats(args.campaign_id)

        if not stats:
            print(f"Campaign {args.campaign_id} not found")
            return

        print("\n" + "=" * 60)
        print(f"Campaign: {stats['name']}")
        print("=" * 60)
        print(f"  ID: {stats['campaign_id']}")
        print(f"  Status: {stats['status']}")
        print(f"  Total Recipients: {stats['total_recipients']}")
        print(f"  Emails Sent: {stats['emails_sent']}")
        print(f"  Emails Delivered: {stats['emails_delivered']}")
        print(f"  Emails Opened: {stats['emails_opened']}")
        print(f"  Emails Clicked: {stats['emails_clicked']}")
        print(f"  Emails Failed: {stats['emails_failed']}")
        print(f"  Open Rate: {stats['open_rate']}")
        print(f"  Click Rate: {stats['click_rate']}")
        print(f"  Created: {stats['created_at']}")
        if stats['started_at']:
            print(f"  Started: {stats['started_at']}")
        if stats['completed_at']:
            print(f"  Completed: {stats['completed_at']}")
        print("=" * 60)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Email campaign management',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create template
    template_parser = subparsers.add_parser('create-template', help='Create email template')
    template_parser.add_argument('--name', required=True, help='Template name')
    template_parser.add_argument('--subject', required=True, help='Email subject')
    template_parser.add_argument('--body-text', required=True, help='Plain text body')
    template_parser.add_argument('--body-html', help='HTML body')
    template_parser.add_argument('--template-type', default='initial',
                                  choices=['initial', 'follow_up', 'custom'],
                                  help='Template type')

    # Create campaign
    campaign_parser = subparsers.add_parser('create-campaign', help='Create email campaign')
    campaign_parser.add_argument('--name', required=True, help='Campaign name')
    campaign_parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    campaign_parser.add_argument('--sender-email', required=True, help='Sender email')
    campaign_parser.add_argument('--sender-name', help='Sender name')
    campaign_parser.add_argument('--description', help='Campaign description')
    campaign_parser.add_argument('--country', help='Filter by country')
    campaign_parser.add_argument('--source', help='Filter by source')
    campaign_parser.add_argument('--industry', help='Filter by industry')
    campaign_parser.add_argument('--follow-up', action='store_true', help='Enable follow-ups')
    campaign_parser.add_argument('--follow-up-days', type=int, default=3,
                                  help='Days before follow-up')
    campaign_parser.add_argument('--follow-up-template-id', type=int,
                                  help='Follow-up template ID')

    # Queue campaign
    queue_parser = subparsers.add_parser('queue', help='Queue emails for campaign')
    queue_parser.add_argument('campaign_id', type=int, help='Campaign ID')
    queue_parser.add_argument('--from-latest-run', action='store_true',
                               help='Queue from latest Apify run')
    queue_parser.add_argument('--limit', type=int, default=100, help='Max leads to queue')

    # Schedule follow-ups
    follow_up_parser = subparsers.add_parser('schedule-follow-ups',
                                              help='Schedule follow-up emails')
    follow_up_parser.add_argument('campaign_id', type=int, help='Campaign ID')

    # Show stats
    stats_parser = subparsers.add_parser('stats', help='Show campaign statistics')
    stats_parser.add_argument('campaign_id', type=int, help='Campaign ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    commands = {
        'create-template': create_template,
        'create-campaign': create_campaign,
        'queue': queue_campaign,
        'schedule-follow-ups': schedule_follow_ups,
        'stats': show_stats
    }

    command_func = commands.get(args.command)
    if command_func:
        command_func(args)


if __name__ == '__main__':
    main()
