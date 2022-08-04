def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'id': user.id,
        'user': user.username,
        'last_login': user.last_login,
        'token': "Bearer " + token,
        'email': user.email
    }
