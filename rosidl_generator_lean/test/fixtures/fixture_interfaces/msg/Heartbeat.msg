# A node reporting that it is alive, and how loaded it is.
std_msgs/Header header

# The node's fully qualified name, e.g. /robot/planner.
string node_name

# Increments once per heartbeat; wraps at 2^32.
uint32 sequence

# One-, five- and fifteen-minute load averages.
float64[3] load

bool healthy
