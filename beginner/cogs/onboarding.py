from beginner.cog import Cog
from beginner.colors import *
from beginner.scheduler import schedule
from beginner.tags import tag
from datetime import timedelta, datetime
import asyncio
import discord
import random


class OnBoarding(Cog):
    async def ready(self):
        self.schedule_onboarding()
        await self.scan_for_unwelcomed_members()

    def schedule_onboarding(self):
        now_utc = datetime.utcnow()
        next_onboarding = (now_utc + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        schedule(
            "new-member-onboarding",
            next_onboarding,
            self.onboard_new_members,
            no_duplication=True,
        )

    @tag("schedule", "onboard-new-members")
    async def onboard_new_members(self):
        self.logger.debug("Onboarding new members")

        found = 0
        onboarding = 0
        role = self.get_role("new member")

        # Onboard all users who have been members for at least 48 hours
        for member in self.server.members:
            if role in member.roles:
                found += 1
                if await self.member_can_be_onboarded(member):
                    await member.remove_roles(
                        role, reason="Onboard recently active member"
                    )
                    onboarding += 1

        # Log results
        self.logger.debug(f"Found {found} new members, {onboarding} were onboarded")
        await self.get_channel("mod-action-log").send(
            embed=discord.Embed(
                color=BLUE,
                description=f"Found {found} new members, {onboarding} were onboarded",
            ).set_author(name="Onboarding New Members", icon_url=self.server.icon_url)
        )

        # Schedule next onboarding
        self.schedule_onboarding()

    async def member_can_be_onboarded(self, member: discord.Member):
        return (datetime.utcnow() - member.joined_at).days >= 2

    @Cog.listener()
    async def on_member_update(
        self, old_member: discord.Member, updated_member: discord.Member
    ):
        if updated_member.pending or not old_member.pending:
            return

        await self.welcome_member(updated_member)

    async def scan_for_unwelcomed_members(self):
        self.logger.debug("Scanning for unwelcomed members")
        members = [
            member
            for member in self.server.members
            if not member.pending and len(member.roles) == 1
        ]
        if not members:
            self.logger.debug("All members have been welcomed")
            return

        self.logger.debug(f"{len(members)} have not been welcomed")
        await self.get_channel("staff").send(
            f"I just restarted and found {len(members)} who accepted the rules while I was away. I'll welcome them now."
        )

        for member in members:
            await self.welcome_member(member)
            await asyncio.sleep(1)

    async def welcome_member(self, member: discord.Member):
        self.logger.debug(f"Welcoming {member.display_name}")
        welcome_messages = [
            "Everybody say hi to {}!!!",
            "Say hello to our newest member {}!!!",
            "Welcome to our newest & coolest member {}!!!",
            "Hey hey hey!!! {} has joined the party!!!",
        ]
        await self.get_channel("🙋hello-world").send(
            random.choice(welcome_messages).format(member.mention)
        )

        await member.add_roles(self.get_role("coders"), self.get_role("new member"))


def setup(client):
    client.add_cog(OnBoarding(client))
