class ThemeEngine:
    def select_theme(self, node: dict) -> str:
        """
        Selects the UI theme for a node.
        Returns: 'community_recipe' | 'campaign_official' | 'location_based'
        """
        governed_by = node.get('governed_by')
        campaign_context = node.get('campaign_context')

        if governed_by == 'brand_official':
            return 'campaign_official'
        elif campaign_context and campaign_context.get('location_data'):
            return 'location_based'
        else:
            return 'community_recipe'

theme_engine = ThemeEngine()
