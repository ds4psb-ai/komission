from enum import Enum

class NodeLayer(Enum):
    MASTER = "master"
    FORK = "fork"
    FORK_OF_FORK = "fork_of_fork"

class NodePermission(Enum):
    READ_ONLY = "read_only"
    FULL_EDIT = "full_edit"
    CAMPAIGN_PROTECTED = "campaign_protected"

class NodeGoverned(Enum):
    OPEN_COMMUNITY = "open_community"
    BRAND_OFFICIAL = "brand_official"
    CREATOR_VERIFIED = "creator_verified"

class GovernanceEngine:
    def check_user_permission(self, user: dict, node: dict, action: str) -> dict:
        """
        Determines if a user can perform an action on a node.
        """
        # Simplify checking for MVP
        is_owner = node.get('created_by') == user.get('id')
        layer = node.get('layer', NodeLayer.FORK.value)
        permission = node.get('permission', NodePermission.FULL_EDIT.value)
        governed_by = node.get('governed_by', NodeGoverned.OPEN_COMMUNITY.value)

        # Master nodes are generally read-only for non-owners
        if layer == NodeLayer.MASTER.value and not is_owner:
            if action in ['edit', 'delete']:
                return {
                    "allowed": False,
                    "reason": "Master nodes are read-only for the community. Fork it to edit!"
                }

        # Brand Official campaigns are protected
        if governed_by == NodeGoverned.BRAND_OFFICIAL.value:
             if action == 'edit' and not is_owner:
                 return {
                     "allowed": False,
                     "reason": "Official Brand Campaign. Protected from direct edits."
                 }

        return {"allowed": True}

governance_engine = GovernanceEngine()
