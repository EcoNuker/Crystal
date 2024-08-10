import string, secrets, asyncio
import guilded
from guilded.ext import commands

from typing import List

from DATA import custom_events


def gen_cryptographically_secure_string(size: int):
    """
    Generates a cryptographically secure string.
    """
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    f = "".join(secrets.choice(letters) for i in range(size))
    return f


class BypassFailed(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def channel_mention(channel: guilded.abc.ServerChannel):
    return f"[#{channel.name}]({channel.share_url})"


def missing_perms(error: guilded.Forbidden):
    permmap = {
        "CanUpdateServer": "Update Server",
        "CanManageRoles": "Manage Roles",
        "CanInviteMembers": "Invite Members",
        "CanKickMembers": "Kick / Ban Members",
        "CanManageGroups": "Manage Groups",
        "CanManageChannels": "Manage Channels",
        "CanManageWebhooks": "Manage Webhooks",
        "CanMentionEveryone": "Can Mention @everyone and @here",
        "CanModerateChannels": "Access Moderator View",
        "CanBypassSlowMode": "Slowmode Exception",
        "CanReadApplications": "View Applications",
        "CanApproveApplications": "Approve Applications",
        "CanEditApplicationForm": "Edit Application Forms",
        "CanIndicateLfmInterest": "Indicate Find Players Interest",
        "CanModifyLfmStatus": "Modify Find Players Status",
        "CanReadAnnouncements": "View Announcements",
        "CanCreateAnnouncements": "Create and Remove Announcements",
        "CanManageAnnouncements": "Manage Announcements",
        "CanReadChats": "Read Messages",
        "CanCreateChats": "Send Messages",
        "CanUploadChatMedia": "Upload Media",
        "CanCreateThreads": "Create Threads",
        "CanCreateThreadMessages": "Send Messages in Threads",
        "CanCreatePrivateMessages": "Send Private Messages",
        "CanManageChats": "Manage Messages",
        "CanManageThreads": "Manage Threads",
        "CanCreateChatForms": "Create Polls and Forms",
        "CanReadEvents": "View Events",
        "CanCreateEvents": "Create Events",
        "CanEditEvents": "Manage Events",
        "CanDeleteEvents": "Remove Events",
        "CanEditEventRsvps": "Edit RSVPs",
        "CanReadForums": "Read Forums",
        "CanCreateTopics": "Create Forum Topics",
        "CanCreateTopicReplies": "Create Topic Replies",
        "CanDeleteTopics": "Manage Topics",
        "CanStickyTopics": "Sticky Topics",
        "CanLockTopics": "Lock Topics",
        "CanReadDocs": "View Docs",
        "CanCreateDocs": "Create Docs",
        "CanEditDocs": "Manage Docs",
        "CanDeleteDocs": "Remove Docs",
        "CanReadMedia": "See Media",
        "CanAddMedia": "Create Media",
        "CanEditMedia": "Manage Media",
        "CanDeleteMedia": "Remove Media",
        "CanListenVoice": "Hear Voice",
        "CanAddVoice": "Add Voice",
        "CanManageVoiceGroups": "Manage Voice Rooms",
        "CanAssignVoiceGroup": "Move Members",
        "CanDisconnectUsers": "Disconnect User",
        "CanBroadcastVoice": "Broadcast",
        "CanDirectVoice": "Whisper",
        "CanPrioritizeVoice": "Priority Speaker",
        "CanUseVoiceActivity": "Use Voice Activity",
        "CanMuteMembers": "Mute Members",
        "CanDeafenMembers": "Deafen Members",
        "CanSendVoiceMessages": "Send Messages in Voice Channel",
        "CanCreateScrims": "Create Scrims",
        "CanManageTournaments": "Manage Tournaments",
        "CanRegisterForTournaments": "Register for Tournaments",
        "CanManageEmotes": "Manage Emoji",
        "CanChangeNickname": "Change Nickname",
        "CanManageNicknames": "Manage Nicknames",
        "CanViewFormResponses": "View Form Responses",
        "CanViewPollResponses": "View Poll Results",
        "CanReadListItems": "View List Items",
        "CanCreateListItems": "Create List Items",
        "CanUpdateListItems": "Manage List Item Messages",
        "CanDeleteListItems": "Remove List Items",
        "CanCompleteListItems": "Complete List Items",
        "CanReorderListItems": "Reorder List Items",
        "CanViewBracket": "View Brackets",
        "CanReportScores": "Report Scores",
        "CanReadSchedules": "View Schedules",
        "CanCreateSchedule": "Create Schedule",
        "CanDeleteSchedule": "Delete Schedule",
        "CanManageBots": "Manage Bots",
        "CanManageServerXp": "Manage Server XP",
        "CanReadStreams": "View Streams",
        "CanJoinStreamVoice": "Join Voice in Streams",
        "CanCreateStreams": "Add Stream",
        "CanSendStreamMessages": "Send Messages in Streams",
        "CanAddStreamVoice": "Add Voice in Streams",
        "CanUseVoiceActivityInStream": "Use Voice Activity in Streams",
    }
    if error.raw_missing_permissions:
        allperms = [permmap[perm.strip()] for perm in error.raw_missing_permissions]
    else:
        allperms = ["UNKNOWN"]
    return allperms


def remove_first_prefix(s: str, prefixes: List[str]) -> str:
    for prefix in prefixes:
        if s.startswith(prefix):
            return s.removeprefix(prefix)
    return s


async def check_higher_member(
    server: guilded.Server, members: List[guilded.Member]
) -> List[guilded.Member]:
    """
    Usually returns a single [guilded.Member] but can be multiple if they're equal.
    """
    await server.fill_roles()
    highest_role = 0
    mems = []
    for member in members:
        # This function seems to work without this, but it's better to handle it
        if not isinstance(member, guilded.Member):
            continue
        if member.is_owner():
            return [member]
        else:
            top_role = await get_highest_role_position(server, member, fill=False)

            if top_role and highest_role < top_role.position:
                highest_role = top_role.position
                mems = [member]
            elif top_role and highest_role == top_role.position:
                mems.append(member)
    if mems == []:
        return [member]
    return mems


async def get_highest_role_position(
    server: guilded.Server, member: guilded.Member, fill: bool = True
) -> guilded.Role | None:
    """
    The higher the role's position, the higher it is on the hierarchy
    """
    if fill:
        await server.fill_roles()
    member_roles = member.roles

    # TODO: make this more efficient, made this in morning with sleep brain :ded:
    highest = 0
    c_role = None

    for role in member_roles:
        if role.position > highest:
            c_role = role
            highest = role.position

    return c_role


async def get_response(ctx: commands.Context, timeout: int = 30) -> guilded.Message:
    """
    Gets the response by waiting for a message in the same channel from the same author.
    """
    try:
        response = await ctx.bot.wait_for(
            "message",
            check=lambda m: m.message.author.id == ctx.author.id
            and m.message.channel.id == ctx.channel.id,
            # and msg.id in m.message.replied_to_ids,
            timeout=timeout,
        )
        return response
    except asyncio.TimeoutError:
        return False


async def check_bypass(
    ctx: commands.Context,
    msg: guilded.Message,
    bypassed: str = "PERMS",
    auto_bypassable: bool = True,
) -> bool:
    """
    Checks bot owner/developer bypass. Used for debugging. Will be flagged in console.

    returns bool: true means continue with operation
    """
    if not ctx.bot.bypassing:
        return False
    if (ctx.author.id in ctx.bot.auto_bypass) and auto_bypassable:
        await asyncio.sleep(
            1
        )  # Guilded is weird here, since it will occasionally return 404 Message Not Found
        await msg.delete()
        return True
    elif ctx.author.id in ctx.bot.owner_ids:
        try:
            bypass = await ctx.bot.wait_for(
                "message",
                check=lambda m: m.message.author.id == ctx.author.id
                and m.message.channel.id == ctx.channel.id
                and msg.id in m.message.replied_to_ids
                and m.message.content.lower().strip() == "bypass",
                timeout=5,
            )
            custom_events.eventqueue.add_overwrites(
                {"message_ids": [msg.id, bypass.message.id]}
            )
            await msg.delete()
            try:
                await bypass.message.delete()
            except:
                pass
            ctx.bot.bypasses[ctx.author.id] = ctx.bot.bypasses.get(ctx.author.id, [])
            ctx.message.bypassed = bypassed
            ctx.bot.bypasses[ctx.author.id].append(ctx.message)
            return True
        except asyncio.TimeoutError:
            return False
    else:
        return False
