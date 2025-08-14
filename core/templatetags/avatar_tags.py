from django import template
import hashlib

register = template.Library()

@register.filter
def get_avatar_color_class(user_id):
    """
    Returns a consistent color class based on the user's ID.
    """
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    # Use a hash of the user's ID to get a deterministic index
    color_index = int(hashlib.sha1(str(user_id).encode('utf-8')).hexdigest(), 16) % len(colors)
    return f'default-avatar-{colors[color_index]}'