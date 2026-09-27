"""
Labeled evaluation set: 25 task pairs with KNOWN ground truth.

Each entry is one "new task" being evaluated against a small pool of
"existing tasks". label=True means this pair SHOULD be suggested as a
dependency (existing task is genuinely a prerequisite of the new task,
based on the text). label=False means it should NOT be suggested --
these are deliberately similar-sounding but unrelated pairs, to test
whether the AI over-triggers on superficial keyword overlap.

This is hand-labeled by us (the developer), based on plain reading of
the text -- it is the ground truth we measure the AI against.
"""

EVAL_DATASET = [
    # ---- Genuine dependencies (label=True) ----
    {
        "id": 1,
        "existing_task": {
            "title": "Design database schema",
            "description": "Define tables for users, orders, products.",
        },
        "new_task": {
            "title": "Build REST API",
            "description": "Implement CRUD endpoints using the database schema.",
        },
        "label": True,
    },
    {
        "id": 2,
        "existing_task": {
            "title": "Set up CI pipeline",
            "description": "Configure GitHub Actions to run tests on push.",
        },
        "new_task": {
            "title": "Deploy to production",
            "description": "Deploy only after CI pipeline passes all checks.",
        },
        "label": True,
    },
    {
        "id": 3,
        "existing_task": {
            "title": "Write authentication middleware",
            "description": "JWT-based auth check for protected routes.",
        },
        "new_task": {
            "title": "Build user profile page",
            "description": "Page requires the user to be authenticated via the auth middleware.",
        },
        "label": True,
    },
    {
        "id": 4,
        "existing_task": {
            "title": "Create wireframes",
            "description": "Low-fidelity mockups for the checkout flow.",
        },
        "new_task": {
            "title": "Implement checkout UI",
            "description": "Build the checkout screen based on the approved wireframes.",
        },
        "label": True,
    },
    {
        "id": 5,
        "existing_task": {
            "title": "Procure server hardware",
            "description": "Order rack servers for the data center.",
        },
        "new_task": {
            "title": "Install OS on servers",
            "description": "Install Linux on the newly procured servers.",
        },
        "label": True,
    },
    {
        "id": 6,
        "existing_task": {
            "title": "Foundation work",
            "description": "Pour concrete foundation for the house.",
        },
        "new_task": {
            "title": "Build walls",
            "description": "Construct walls once the foundation has cured.",
        },
        "label": True,
    },
    {
        "id": 7,
        "existing_task": {
            "title": "Electrical wiring",
            "description": "Run wiring through the walls.",
        },
        "new_task": {
            "title": "Install drywall",
            "description": "Cover walls with drywall after wiring is complete.",
        },
        "label": True,
    },
    {
        "id": 8,
        "existing_task": {
            "title": "Write unit tests for payment module",
            "description": "Cover edge cases in the payment calculation logic.",
        },
        "new_task": {
            "title": "Release payment module to staging",
            "description": "Only release once unit tests for payment are passing.",
        },
        "label": True,
    },
    {
        "id": 9,
        "existing_task": {
            "title": "Get legal approval for contract terms",
            "description": "Legal team reviews the vendor contract.",
        },
        "new_task": {
            "title": "Sign vendor contract",
            "description": "Sign the contract after legal approval is granted.",
        },
        "label": True,
    },
    {
        "id": 10,
        "existing_task": {
            "title": "Collect customer requirements",
            "description": "Interview stakeholders for feature requirements.",
        },
        "new_task": {
            "title": "Write technical spec",
            "description": "Draft the spec based on the collected customer requirements.",
        },
        "label": True,
    },
    {
        "id": 11,
        "existing_task": {
            "title": "Train the ML model",
            "description": "Train a classifier on the labeled dataset.",
        },
        "new_task": {
            "title": "Deploy model to production",
            "description": "Deploy the trained model behind an API.",
        },
        "label": True,
    },
    {
        "id": 12,
        "existing_task": {
            "title": "Purchase domain name",
            "description": "Buy taskflowpro.com from a registrar.",
        },
        "new_task": {
            "title": "Configure DNS records",
            "description": "Point the purchased domain to the server IP.",
        },
        "label": True,
    },
    {
        "id": 13,
        "existing_task": {
            "title": "Design app logo",
            "description": "Create the brand logo in Figma.",
        },
        "new_task": {
            "title": "Add logo to app header",
            "description": "Insert the finalized logo into the navbar component.",
        },
        "label": True,
    },
    # ---- Non-dependencies (label=False) -- similar wording, no real link ----
    {
        "id": 14,
        "existing_task": {
            "title": "Design database schema",
            "description": "Define tables for users, orders, products.",
        },
        "new_task": {
            "title": "Write marketing copy",
            "description": "Draft homepage text for the landing page.",
        },
        "label": False,
    },
    {
        "id": 15,
        "existing_task": {
            "title": "Set up CI pipeline",
            "description": "Configure GitHub Actions to run tests on push.",
        },
        "new_task": {
            "title": "Plan team offsite",
            "description": "Book venue for the quarterly team offsite.",
        },
        "label": False,
    },
    {
        "id": 16,
        "existing_task": {
            "title": "Foundation work",
            "description": "Pour concrete foundation for the house.",
        },
        "new_task": {
            "title": "Choose paint colors",
            "description": "Pick paint swatches for the bedroom -- purely aesthetic decision, independent of construction phase.",
        },
        "label": False,
    },
    {
        "id": 17,
        "existing_task": {
            "title": "Write unit tests for payment module",
            "description": "Cover edge cases in the payment calculation logic.",
        },
        "new_task": {
            "title": "Design employee onboarding doc",
            "description": "Write a welcome guide for new hires.",
        },
        "label": False,
    },
    {
        "id": 18,
        "existing_task": {
            "title": "Train the ML model",
            "description": "Train a classifier on the labeled dataset.",
        },
        "new_task": {
            "title": "Renew office lease",
            "description": "Sign the annual lease renewal with the landlord.",
        },
        "label": False,
    },
    {
        "id": 19,
        "existing_task": {
            "title": "Purchase domain name",
            "description": "Buy taskflowpro.com from a registrar.",
        },
        "new_task": {
            "title": "Design app logo",
            "description": "Create the brand logo in Figma -- unrelated to domain purchase.",
        },
        "label": False,
    },
    {
        "id": 20,
        "existing_task": {
            "title": "Electrical wiring",
            "description": "Run wiring through the walls.",
        },
        "new_task": {
            "title": "Order kitchen appliances",
            "description": "Buy a fridge and oven for the kitchen, to be installed much later.",
        },
        "label": False,
    },
    {
        "id": 21,
        "existing_task": {
            "title": "Get legal approval for contract terms",
            "description": "Legal team reviews the vendor contract.",
        },
        "new_task": {
            "title": "Organize company picnic",
            "description": "Plan the annual summer picnic for employees.",
        },
        "label": False,
    },
    {
        "id": 22,
        "existing_task": {
            "title": "Collect customer requirements",
            "description": "Interview stakeholders for feature requirements.",
        },
        "new_task": {
            "title": "Fix office printer",
            "description": "Call IT support to fix the jammed printer.",
        },
        "label": False,
    },
    {
        "id": 23,
        "existing_task": {
            "title": "Create wireframes",
            "description": "Low-fidelity mockups for the checkout flow.",
        },
        "new_task": {
            "title": "Renew SSL certificate",
            "description": "Renew the expiring SSL cert for the main domain.",
        },
        "label": False,
    },
    {
        "id": 24,
        "existing_task": {
            "title": "Procure server hardware",
            "description": "Order rack servers for the data center.",
        },
        "new_task": {
            "title": "Write API documentation",
            "description": "Document the public REST API endpoints for developers.",
        },
        "label": False,
    },
    {
        "id": 25,
        "existing_task": {
            "title": "Write authentication middleware",
            "description": "JWT-based auth check for protected routes.",
        },
        "new_task": {
            "title": "Choose office furniture",
            "description": "Order desks and chairs for the new office.",
        },
        "label": False,
    },
]
