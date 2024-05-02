# Maybe use hurl for integration testing, hook up to BDD somehow?
# Having a play with hurl
POST http://localhost:8000/events/
[{
"type": "user",
"timestamp": "2023-10-01T13:45:00.000Z",
"event_id": "{{event_id}}",
"event": {
"username": "my_user",
"email": "my_user@email.com",
"operation": "read/write"
}
},{
"type": "user",
"timestamp": "2025-10-01T13:45:00.000Z",
"event_id": "{{event_id}}11",
"event": {
"username": "my_user",
"email": "my_user@email.com",
"operation": "read/write"
}
}]

# GET http://localhost:8000/events/blah
