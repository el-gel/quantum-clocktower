from networkx import DiGraph

# TODO: global game state, not just players. For e.g. minstrel
def droisoned_tokens(players):
    """Which tokens are hidden in this state due to droisoning?

This is not the same as which players are droisoned; in droison loops,
tokens pointing outside of the loop are hidden, but ones making the loop aren't"""
    # Graph of players that are trying to droison, edges as tokens they use
    graph = DiGraph()
    for player in players:
        for other, token in player.droisoning_tokens():
            graph.add_edge(player, other, token=token)
    # TODO: This allows self-droisoning players that are trying to droison others
    #   to still do their droisoning
    # This shouldn't be possible with real characters, but consider preparse
    
    # Now look for any players which aren't being pointed at: we know they're sober
    # Hide all the tokens from players they point to, and remove them from graph as well
    # Repeat until noone in the graph is a known sober player
    ret = []
    while sober := [p for p,d in graph.in_degree() if d == 0]:
        for player in sober:
            for droisoned in list(graph.adj[player]):
                # This player is droisoned, so hide all tokens they put down
                ret.append((droisoned, droisoned.placed_reminders))
                # They won't be part of loops, remove from graph
                graph.remove_node(droisoned)
            # Then remove this player from the graph
            graph.remove_node(player)
    # All remaining players are being pointed at by someone
    # But they also point at someone
    # So they must be part of a loop (potentially multiple, or self applying)
    # The tokens that are part of the loop are not hidden, but the others are
    for droisoned in graph:
        to_remove = []
        for other, token in droisoned.placed_reminders:
            # Check if this (other, token) pair is in the graph
            if other in graph.adj[droisoned] and graph.adj[droisoned][other]["token"] == token:
                continue
            # It's not, so not part of the loop; mark hidden
            to_remove.append((other,token))
        if to_remove:
            ret.append((droisoned, to_remove))
    return ret
