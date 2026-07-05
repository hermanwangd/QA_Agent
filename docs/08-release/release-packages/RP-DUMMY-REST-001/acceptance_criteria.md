acceptance_criteria:
  - ac_id: RP-DUMMY-REST-001-AC-001
    title: Dummy order creation accepts a valid order request
    classification: automatable
    description: >
      A valid order creation request sent to the dummy REST provider returns an
      accepted order response with the requested customer identifier.
    source_ref: dummy_app.app#create_order
