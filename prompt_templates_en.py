prompt_templates = {
    "Standard": {
        "template": (
            "**As an analyst with 10 years of experience and expertise in PlantUML notation, prepare a {diagram_type} diagram in PlantUML notation for the process:**\n\n"
            "{process_description}\n\n"
            "**Requirements:**\n"
            "- Format: Complete PlantUML code (@startuml ... @enduml)\n"
            "- Include all process participants\n"
            "- Maintain logical sequence of steps\n\n"
            "**Output:** Ready-to-use PlantUML code"
        ),
        "allowed_diagram_types": "all",  # or list e.g. ["sequence", "activity", ...]
        "type": "PlantUML"
    },
    "Sequence Diagram": {
        "template": (
            "Based on the business process description: {process_description}\n\n"

            "**STEP 1: BUSINESS PROCESS ANALYSIS**\n"
            "Analyze the described process and identify:\n"
            "- Who initiates the process (main actor)?\n"
            "- What are the consecutive process steps in chronological order?\n"
            "- Which roles/systems participate in each step?\n"
            "- What data is passed between participants?\n"
            "- Where do decisions/conditions occur in the process?\n"
            "- What are the alternative paths (errors, exceptions)?\n"
            "- Are there asynchronous or parallel operations?\n"
            "- Where does the process end for different scenarios?\n\n"

            "**STEP 2: SEQUENCE PARTICIPANTS IDENTIFICATION**\n"
            "Based on the analysis, determine all process participants:\n\n"

            "**A) HUMAN ACTORS:**\n"
            "- Who is the process initiator?\n"
            "- Who makes decisions during the process?\n"
            "- Who receives results/notifications?\n"
            "- Are there different roles with different permissions?\n\n"

            "**B) INTERNAL SYSTEMS:**\n"
            "- Which applications/services handle the process?\n"
            "- Which components communicate with each other?\n"
            "- Which databases are used?\n"
            "- Are there notification/reporting systems?\n\n"

            "**C) EXTERNAL SYSTEMS:**\n"
            "- Which external APIs need to be communicated with?\n"
            "- Which systems provide reference data?\n"
            "- Which systems receive notifications?\n"
            "- Are there payment/verification systems?\n\n"

            "**D) INFRASTRUCTURE COMPONENTS:**\n"
            "- Are there message queues?\n"
            "- Are there cache/storage services?\n"
            "- Are there API gateways?\n"
            "- Are there audit/logging services?\n\n"

            "**STEP 3: MAPPING PROCESS STEPS TO INTERACTIONS**\n"
            "For each business process step, determine:\n\n"

            "**A) MAIN FLOW (HAPPY PATH):**\n"
            "- Who initiates each step?\n"
            "- To whom/what is the message sent?\n"
            "- What is the communication type (synchronous/asynchronous)?\n"
            "- What data is passed?\n"
            "- Are responses/confirmations returned?\n\n"

            "**B) CONDITIONAL FLOWS:**\n"
            "- Where do if/else conditions occur?\n"
            "- What are the decision criteria?\n"
            "- How do paths differ for different conditions?\n\n"

            "**C) ERROR FLOWS:**\n"
            "- What happens with validation errors?\n"
            "- How are system errors handled?\n"
            "- Are there retry/compensation mechanisms?\n\n"

            "**D) PARALLEL OPERATIONS:**\n"
            "- Which operations can be executed simultaneously?\n"
            "- Where are synchronization points?\n"
            "- Are there background asynchronous operations?\n\n"

            "**STEP 4: PLANTUML DIAGRAM GENERATION**\n"
            "Generate complete PlantUML code in basic notation with the following requirements:\n\n"

            "**TECHNICAL STRUCTURE:**\n"
            "1. **Start:** `@startuml`\n"
            "2. **Title:** `title [Process Name] - Interaction Sequence`\n"
            "3. **Participant definitions before sequence**\n"
            "4. **Logical interaction order**\n"
            "5. **End:** `@enduml`\n\n"

            "**PARTICIPANTS TO USE:**\n"
            "- `actor \"Name\" as alias` - users/business roles\n"
            "- `participant \"Name\" as alias` - internal systems/applications\n"
            "- `entity \"Name\" as alias` - databases/storage\n"
            "- `boundary \"Name\" as alias` - interfaces/API\n"
            "- `control \"Name\" as alias` - controllers/services\n"
            "- `collections \"Name\" as alias` - data collections/lists\n"
            "- `queue \"Name\" as alias` - message queues\n"
            "- `database \"Name\" as alias` - external systems\n\n"

            "**ARROW TYPES AND COMMUNICATION:**\n"
            "- `->` - synchronous call\n"
            "- `-->` - synchronous response\n"
            "- `->>` - asynchronous call\n"
            "- `-->>` - asynchronous response\n"
            "- `-x` - call ending with error\n"
            "- `--x` - error response\n\n"

            "**FLOW CONTROL ELEMENTS:**\n"
            "- `alt [condition]` / `else [condition]` / `end` - conditions\n"
            "- `opt [condition]` / `end` - optional operations\n"
            "- `loop [condition]` / `end` - loops\n"
            "- `par` / `and` / `end` - parallel operations\n"
            "- `critical` / `end` - critical sections\n"
            "- `break [condition]` / `end` - sequence interruption\n\n"

            "**ADDITIONAL ELEMENTS:**\n"
            "- `activate alias` / `deactivate alias` - participant activation\n"
            "- `note left/right/over alias : text` - explanatory notes\n"
            "- `ref over alias1, alias2 : Process name` - references to sub-processes\n"
            "- `group [group name]` / `end` - logical grouping\n"
            "- `|||` - time break\n"
            "- `... text ...` - break with description\n\n"

            "**STRUCTURE EXAMPLE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "title [Process Name] - Interaction Sequence\n\n"

            "' Process participants\n"
            "actor \"[Initiating Role]\" as user\n"
            "boundary \"[Process] Web Interface\" as web\n"
            "control \"[Process] Controller\" as controller\n"
            "control \"[Function] Service\" as service\n"
            "entity \"[Process] Repository\" as repo\n"
            "database \"[Process] Database\" as db\n"
            "participant \"[External] System\" as external\n"
            "actor \"[Target Role]\" as target_user\n\n"

            "' Main process flow\n"
            "user -> web : 1. Initiates [operation name]\n"
            "activate web\n"
            "web -> controller : 2. Passes request\n"
            "activate controller\n\n"

            "controller -> service : 3. Calls business logic\n"
            "activate service\n\n"

            "' Validation/checks\n"
            "service -> repo : 4. Checks conditions\n"
            "activate repo\n"
            "repo -> db : SQL: SELECT ...\n"
            "db --> repo : data\n"
            "repo --> service : check result\n"
            "deactivate repo\n\n"

            "' Business conditions\n"
            "alt [condition met]\n"
            "    service -> external : 5a. Calls external system\n"
            "    external --> service : confirmation\n"
            "    \n"
            "    service -> repo : 6a. Saves result\n"
            "    activate repo\n"
            "    repo -> db : SQL: INSERT/UPDATE ...\n"
            "    db --> repo : confirmation\n"
            "    repo --> service : success\n"
            "    deactivate repo\n"
            "else [condition not met]\n"
            "    service -> service : 5b. Alternative logic\n"
            "    note right : Handling exceptional case\n"
            "end\n\n"

            "service --> controller : operation result\n"
            "deactivate service\n"
            "controller --> web : response\n"
            "deactivate controller\n"
            "web --> user : 7. Confirmation/message\n"
            "deactivate web\n\n"

            "' Notifications (asynchronous)\n"
            "opt [if notification required]\n"
            "    service ->> target_user : 8. Notification about [event]\n"
            "    note right : Asynchronous notification\n"
            "end\n\n"

            "@enduml\n"
            "```\n\n"

            "**NUMBERING AND DESCRIPTION RULES:**\n"
            "- Number consecutive interactions for better readability (1., 2., 3...)\n"
            "- Message descriptions should reflect business language from the process\n"
            "- Use active verbs (\"creates\", \"checks\", \"confirms\")\n"
            "- Group logically related operations\n"
            "- Add notes for complex logic\n\n"

            "**NAMING CONVENTIONS:**\n"
            "- Participant names should reflect roles from the business process\n"
            "- Use functional names describing purpose, not implementation\n"
            "- Short aliases without spaces (user, payment_service, order_db)\n"
            "- Consistent language (Polish or English)\n"
            "- Message names describe business activity\n\n"

            "**FINAL RESULT:**\n"
            "Deliver complete, working PlantUML code that:\n"
            "1. Shows chronological flow of the business process\n"
            "2. Includes all scenarios (main, alternative, errors)\n"
            "3. Contains appropriate communication types (sync/async)\n"
            "4. Shows participant activation/deactivation\n"
            "5. Is ready to use without modifications\n"
            "6. Contains comments explaining process→sequence mapping\n"
            "7. Reflects actual timing and business process flow"
        ),
        "allowed_diagram_types": ["sequence"],
        "type": "PlantUML"
    },
    "Activity Diagram": {
        "template": (
            "Based on the business process description: {process_description}\n\n"

            "**STEP 1: BUSINESS PROCESS ANALYSIS**\n"
            "Analyze the described process and identify:\n"
            "- What is the process goal and starting point?\n"
            "- What are the main activities/tasks in the process?\n"
            "- Where do decisions and branching points occur?\n"
            "- What are the conditions and decision criteria?\n"
            "- Which activities can be performed in parallel?\n"
            "- Who is responsible for individual activities?\n"
            "- Where can the process end?\n"
            "- What are the exceptions and error paths?\n"
            "- Are there loops/repeating activities?\n\n"

            "**STEP 2: FLOW STRUCTURE IDENTIFICATION**\n"
            "Based on the analysis, determine flow elements:\n\n"

            "**A) START AND END POINTS:**\n"
            "- What initiates the process?\n"
            "- What are the possible process endings?\n"
            "- Are there different entry points?\n"
            "- Are there process interruption points?\n\n"

            "**B) MAIN ACTIVITIES:**\n"
            "- What are the key business activities?\n"
            "- Which activities require human intervention?\n"
            "- Which activities are automatic?\n"
            "- What are the preparatory/final activities?\n\n"

            "**C) DECISIONS AND BRANCHES:**\n"
            "- Where are decisions made?\n"
            "- What are the choice options?\n"
            "- What are the decision criteria?\n"
            "- Are there nested decisions?\n\n"

            "**D) PARALLEL FLOWS:**\n"
            "- Which activities can be performed simultaneously?\n"
            "- Where are synchronization points?\n"
            "- Are there independent activities?\n"
            "- Where should we wait for all paths to complete?\n\n"

            "**E) ROLES AND RESPONSIBILITIES:**\n"
            "- Who performs individual activities?\n"
            "- Are there different roles in the process?\n"
            "- Where does responsibility handover occur?\n"
            "- Are there cross-departmental activities?\n\n"

            "**STEP 3: LOGICAL FLOW MAPPING**\n"
            "For each activity and decision, determine:\n\n"

            "**A) MAIN SEQUENCE:**\n"
            "- What is the natural order of activities?\n"
            "- Which activities are mandatory?\n"
            "- Where are checkpoints?\n"
            "- What are the inputs and outputs of each activity?\n\n"

            "**B) CONDITIONAL PATHS:**\n"
            "- What conditions determine path selection?\n"
            "- Do all paths lead to the same point?\n"
            "- Where are path merge points?\n"
            "- What are the alternative flows?\n\n"

            "**C) EXCEPTION HANDLING:**\n"
            "- What happens in case of errors?\n"
            "- What are the recovery mechanisms?\n"
            "- Are there compensating activities?\n"
            "- Where can the process be interrupted?\n\n"

            "**D) LOOPS AND ITERATIONS:**\n"
            "- Which activities repeat?\n"
            "- What are the loop termination conditions?\n"
            "- Are there nested loops?\n"
            "- Where are the return points?\n\n"

            "**STEP 4: PLANTUML DIAGRAM GENERATION**\n"
            "Generate complete PlantUML code in basic notation with the following requirements:\n\n"

            "**TECHNICAL STRUCTURE:**\n"
            "1. **Start:** `@startuml`\n"
            "2. **Title:** `title [Process Name] - Activity Flow`\n"
            "3. **Theme:** `!theme plain` or omit for default style\n"
            "4. **Logical activity sequence**\n"
            "5. **End:** `@enduml`\n\n"

            "**BASIC ELEMENTS:**\n"
            "- `start` - starting point\n"
            "- `end` - ending point\n"
            "- `stop` - stop point\n"
            "- `:Activity Name;` - activity\n"
            "- `if (condition?) then (yes)` - decision with condition\n"
            "- `else (no)` - alternative\n"
            "- `endif` - end of decision\n"
            "- `while (condition?)` - loop\n"
            "- `endwhile` - end of loop\n"
            "- `repeat` - repeat-until loop\n"
            "- `repeat while (condition?)` - end of repeat loop\n\n"

            "**PARALLEL FLOWS:**\n"
            "- `fork` - start of parallel flows\n"
            "- `fork again` - next parallel flow\n"
            "- `end fork` - end of parallel flows\n"
            "- `split` - alternative branching\n"
            "- `split again` - next branch\n"
            "- `end split` - end of branches\n\n"

            "**ROLES AND GROUPS:**\n"
            "- `|Role Name|` - swimlane for role\n"
            "- `partition \"Group Name\" {{ }}` - activity grouping\n"
            "- `group \"Group Name\"` / `end group` - logical grouping\n\n"

            "**ADDITIONAL ELEMENTS:**\n"
            "- `note left/right : text` - notes\n"
            "- `floating note : text` - floating note\n"
            "- `kill` - immediate termination\n"
            "- `detach` - detachment from main flow\n"
            "- `backward :Activity;` - backward activity\n\n"

            "**COLORS AND STYLES:**\n"
            "- `#LightBlue` - activity color\n"
            "- `#Pink` - decision color\n"
            "- `#LightGreen` - success color\n"
            "- `#Orange` - warning color\n"
            "- `#Red` - error color\n\n"

            "**STRUCTURE EXAMPLE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "!theme plain\n"
            "title [Process Name] - Activity Flow\n\n"

            "start\n\n"

            "' Swimlanes for roles\n"
            "|Initiator|\n"
            ":Start process;\n"
            ":Prepare data;\n\n"

            "' Decision with condition\n"
            "if (Data complete?) then (yes)\n"
            "  |Processor|\n"
            "  :Validate data;\n"
            "  \n"
            "  if (Validation OK?) then (yes)\n"
            "    ' Parallel flow\n"
            "    fork\n"
            "      :Main processing;\n"
            "    fork again\n"
            "      :Generate report;\n"
            "    fork again\n"
            "      :Send notifications;\n"
            "    end fork\n"
            "    \n"
            "    :Finalize process;\n"
            "    \n"
            "  else (no)\n"
            "    :Handle validation errors;\n"
            "    |Initiator|\n"
            "    :Correct data;\n"
            "    \n"
            "    ' Loop for corrections\n"
            "    while (More corrections?) is (yes)\n"
            "      :Make corrections;\n"
            "    endwhile (no)\n"
            "  endif\n"
            "  \n"
            "else (no)\n"
            "  :Obtain missing data;\n"
            "  note right : May require contact\\nwith external sources\n"
            "endif\n\n"

            "' Process completion\n"
            "|Manager|\n"
            ":Review results;\n\n"

            "if (Results acceptable?) then (yes)\n"
            "  :Approve process;\n"
            "  #LightGreen:Process completed successfully;\n"
            "  end\n"
            "else (no)\n"
            "  #Orange:Process requires repetition;\n"
            "  stop\n"
            "endif\n\n"

            "@enduml\n"
            "```\n\n"

            "**NAMING AND DESCRIPTION RULES:**\n"
            "- Activity names should be verbs describing action\n"
            "- Use business language, not technical\n"
            "- Formulate conditions as questions (\"Data correct?\")\n"
            "- Condition responses should be unambiguous (yes/no)\n"
            "- Group logically related activities\n"
            "- Use colors to distinguish activity types\n\n"

            "**STRUCTURE RULES:**\n"
            "- One main flow with branches\n"
            "- Clear decision points with all paths\n"
            "- Minimize line crossings\n"
            "- Group activities by responsibility\n"
            "- Show all possible process endings\n"
            "- Use notes for complex conditions\n\n"

            "**FINAL RESULT:**\n"
            "Deliver complete, working PlantUML code that:\n"
            "1. Shows complete business process flow\n"
            "2. Includes all decisions and alternative paths\n"
            "3. Contains appropriate roles and responsibilities\n"
            "4. Shows parallel flows where needed\n"
            "5. Handles exceptions and error paths\n"
            "6. Is ready to use without modifications\n"
            "7. Contains comments explaining process logic\n"
            "8. Reflects actual sequence and business logic\n"
            "9. Uses appropriate colors for better readability"
        ),
        "allowed_diagram_types": ["activity"],
        "type": "PlantUML"
    },
    "Use Case Diagram": {
        "template": (
            "Based on the business process description: {process_description}\n\n"

            "**STEP 1: ANALYSIS OF BUSINESS FUNCTIONS IN THE PROCESS**\n"
            "Analyze the described process and identify:\n"
            "- Who are the users of the process (roles, actors)?\n"
            "- What business goals are they trying to achieve?\n"
            "- What are the main functions/activities they perform in the process?\n"
            "- What outcomes/values are delivered by the process?\n"
            "- What external systems does the process integrate with?\n"
            "- What are the preconditions and postconditions for each function?\n"
            "- Where do variants/alternatives occur in the process?\n"
            "- What are the exceptions and error situations?\n\n"

            "**STEP 2: IDENTIFICATION OF ACTORS AND USE CASES**\n"
            "Based on the analysis, define the diagram elements:\n\n"

            "**A) PRIMARY ACTORS:**\n"
            "- Who initiates the process and benefits from it?\n"
            "- What business roles are directly involved?\n"
            "- Are there different types of users with different permissions?\n"
            "- Are there actors representing organizations/departments?\n\n"

            "**B) SECONDARY ACTORS:**\n"
            "- What external systems support the process?\n"
            "- What services/APIs are invoked?\n"
            "- Are there automated processes/timers?\n"
            "- What systems provide reference data?\n\n"

            "**C) MAIN USE CASES:**\n"
            "- What are the key business functions of the process?\n"
            "- What tasks do the individual actors perform?\n"
            "- What are the complete end-to-end scenarios?\n"
            "- Which functions provide direct business value?\n\n"

            "**D) SUPPORTING USE CASES:**\n"
            "- What are the auxiliary/administrative functions?\n"
            "- What are the data management functions?\n"
            "- What are the reporting/monitoring functions?\n"
            "- What are the configuration/settings functions?\n\n"

            "**STEP 3: MAPPING RELATIONSHIPS AND DEPENDENCIES**\n"
            "Define relationships between elements:\n\n"

            "**A) RELATIONSHIPS BETWEEN ACTORS:**\n"
            "- Are there role hierarchies (generalization)?\n"
            "- Are there groups of actors with similar functions?\n"
            "- Are there abstract/concrete actors?\n\n"

            "**B) RELATIONSHIPS BETWEEN USE CASES:**\n"
            "- Which use cases share common elements (include)?\n"
            "- Which are optional extensions of others (extend)?\n"
            "- Are there abstract/concrete use cases?\n"
            "- Where do functional specializations occur?\n\n"

            "**C) SYSTEM BOUNDARIES:**\n"
            "- What is inside and outside the system?\n"
            "- What are the boundaries of responsibility?\n"
            "- Which functions are automated and which are manual?\n\n"

            "**STEP 4: GENERATE PlantUML DIAGRAM**\n"
            "Generate complete PlantUML code in use case notation with the following requirements:\n\n"

            "**TECHNICAL STRUCTURE:**\n"
            "1. **Start:** `@startuml`\n"
            "2. **Title:** `title [Process Name] - Use Cases`\n"
            "3. **Define actors before use cases**\n"
            "4. **Group elements within system boundaries**\n"
            "5. **End:** `@enduml`\n\n"

            "**ACTORS TO USE:**\n"
            "- `actor \"Name\" as alias` – business users/roles\n"
            "- `:Name:` – alternative actor notation\n"
            "- `actor \"Name\" <<system>> as alias` – external systems\n"
            "- `actor \"Name\" <<device>> as alias` – devices\n"
            "- `actor \"Name\" <<timer>> as alias` – time-based processes\n\n"

            "**USE CASES:**\n"
            "- `usecase \"Name\" as alias` – main use cases\n"
            "- `(Name)` – alternative notation\n"
            "- `usecase \"Name\" <<system>> as alias` – system functions\n"
            "- `usecase \"Name\" <<report>> as alias` – reporting functions\n\n"

            "**BOUNDARIES AND GROUPING:**\n"
            "- `rectangle \"System Name\" {{ }}` – main system boundaries\n"
            "- `package \"Module\" {{ }}` – functional grouping\n"
            "- `node \"Subsystem\" {{ }}` – subsystems\n"
            "- `frame \"Area\" {{ }}` – business areas\n\n"

            "**RELATIONSHIPS AND CONNECTIONS:**\n"
            "- `-->` – association between actor and use case\n"
            "- `..>` – include/extend relation with label\n"
            "- `--|>` – generalization (inheritance)\n"
            "- `<<include>>` – required inclusion\n"
            "- `<<extend>>` – optional extension\n\n"

            "**STEREOTYPES AND LABELS:**\n"
            "- `<<include>>` – shared functionality\n"
            "- `<<extend>>` – optional extensions\n"
            "- `<<system>>` – automated functions\n"
            "- `<<manual>>` – manual functions\n"
            "- `<<critical>>` – critical functions\n\n"

            "**STRUCTURE EXAMPLE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "title [Process Name] - Use Cases\n\n"

            "' Primary actors from business process\n"
            "actor \"[Main Role]\" as main_user\n"
            "actor \"[Approving Role]\" as approver\n"
            "actor \"Administrator\" as admin\n\n"

            "' Secondary actors (external systems)\n"
            "actor \"[External System]\" <<system>> as external_system\n"
            "actor \"[Notification System]\" <<system>> as notification_system\n\n"

            "' System boundaries\n"
            "rectangle \"System [Process Name]\" {{\n\n"

            "    ' Main use cases from process\n"
            "    package \"Main Functions\" {{\n"
            "        usecase \"[Main Function 1]\" as main_uc1\n"
            "        usecase \"[Main Function 2]\" as main_uc2\n"
            "        usecase \"[Process Approval]\" as approve_uc\n"
            "    }}\n\n"

            "    ' Supporting functions\n"
            "    package \"Supporting Functions\" {{\n"
            "        usecase \"Data Validation\" as validate_uc\n"
            "        usecase \"Generate Report\" as report_uc\n"
            "        usecase \"Send Notification\" as notify_uc\n"
            "    }}\n\n"

            "    ' Administrative functions\n"
            "    package \"Administration\" {{\n"
            "        usecase \"Configuration Management\" as config_uc\n"
            "        usecase \"Process Monitoring\" as monitor_uc\n"
            "    }}\n"
            "}}\n\n"

            "' Actor to use case relationships\n"
            "main_user --> main_uc1 : \"Initiates\"\n"
            "main_user --> main_uc2 : \"Performs\"\n"
            "approver --> approve_uc : \"Approves\"\n"
            "admin --> config_uc : \"Configures\"\n"
            "admin --> monitor_uc : \"Monitors\"\n\n"

            "' Include/extend relationships\n"
            "main_uc1 ..> validate_uc : <<include>>\n"
            "main_uc2 ..> validate_uc : <<include>>\n"
            "approve_uc ..> notify_uc : <<include>>\n"
            "main_uc1 ..> report_uc : <<extend>>\n\n"

            "' Integration with external systems\n"
            "validate_uc --> external_system : \"Verifies\"\n"
            "notify_uc --> notification_system : \"Sends\"\n\n"

            "' Generalizations (if any)\n"
            "main_user --|> approver : \"may also be\"\n\n"

            "' Explanatory notes\n"
            "note right of main_uc1 : \"Main business process flow\"\n"
            "note left of validate_uc : \"Shared validation for all functions\"\n\n"

            "@enduml\n"
            "```\n\n"

            "**NAMING GUIDELINES:**\n"
            "- Use case names as verb phrases (\"Submit Application\", \"Approve Document\")\n"
            "- Actor names as roles/business functions (\"Applicant\", \"Manager\")\n"
            "- Aliases short, no spaces (submit_request, approve_doc)\n"
            "- Consistent language (Polish or English)\n"
            "- Names reflect business value, not technical implementation\n\n"

            "**FUNCTIONAL MODELING PRINCIPLES:**\n"
            "- Each use case represents a complete business function\n"
            "- Actors represent roles, not specific people\n"
            "- System boundaries show scope of responsibility\n"
            "- Use `include` for required shared functions\n"
            "- Use `extend` for optional extensions\n"
            "- Use generalization for role/function hierarchies\n\n"

            "**FINAL RESULT:**\n"
            "Provide complete, working PlantUML code that:\n"
            "1. Reflects all business functions derived from the process\n"
            "2. Shows roles and their interactions with the system\n"
            "3. Includes hierarchies and dependencies between functions\n"
            "4. Defines system boundaries and external integrations\n"
            "5. Is ready to use without modification\n"
            "6. Contains explanatory comments mapping process → functions\n"
            "7. Presents the end-user perspective of the system"
        ),
        "allowed_diagram_types": ["usecase"],
        "type": "PlantUML"
    },
    "Class Diagram": {
        "template": (
            "Based on the business process description: {process_description}\n\n"

            "**STEP 1: BUSINESS PROCESS ANALYSIS**\n"
            "Analyze the described process and identify:\n"
            "- What **NOUNS** (objects/entities) appear in the process?\n"
            "- What **VERBS** (actions/operations) are performed?\n"
            "- What **ADJECTIVES** (properties/attributes) describe the objects?\n"
            "- What **BUSINESS RULES** govern the process?\n"
            "- What **STATES** can objects have in the process?\n"
            "- What **RELATIONSHIPS** exist between objects?\n"
            "- Identify the process name and use it when generating the diagram\n\n"

            "**STEP 2: CLASS AND OBJECT IDENTIFICATION**\n"
            "Based on the analysis, determine which classes are needed:\n\n"

            "**A) ENTITY CLASSES:**\n"
            "- What are the main business objects in the process?\n"
            "- Which nouns represent persistent data?\n"
            "- Which objects have a unique identity?\n"
            "- Which objects are stored in the database?\n"
            "Example: Order, Customer, Product, Invoice\n\n"

            "**B) VALUE OBJECTS:**\n"
            "- Which objects represent values without identity?\n"
            "- Which data is immutable?\n"
            "- Which objects are defined by their attributes?\n"
            "Example: Address, Price, DateTime, OrderStatus\n\n"

            "**C) CONTROL CLASSES:**\n"
            "- Which actions/operations require dedicated classes?\n"
            "- Which processes are complex and require orchestration?\n"
            "- Which business rules are complicated?\n"
            "Example: OrderManager, PriceCalculator, DataValidator\n\n"

            "**D) UTILITY CLASSES:**\n"
            "- Which operations are common to many classes?\n"
            "- Which functions do not belong to a specific object?\n"
            "- Which tools are needed to support the process?\n"
            "Example: DateUtils, StringHelper, Logger\n\n"

            "**E) ENUMERATIONS AND INTERFACES:**\n"
            "- Which values have a limited list of options?\n"
            "- Which behaviors can be implemented differently?\n"
            "- Which contracts need to be defined?\n"
            "Example: enum OrderStatus, interface IPayment\n\n"

            "**STEP 3: ATTRIBUTE AND METHOD ANALYSIS**\n"
            "For each identified class, determine:\n\n"

            "**ATTRIBUTES:**\n"
            "- What **data** does the class store?\n"
            "- Which attributes are **public** (+), **private** (-), **protected** (#)?\n"
            "- What are the data **types** (string, int, decimal, DateTime, etc.)?\n"
            "- Which attributes are **keys** (ID, unique identifiers)?\n"
            "- Which attributes have **default values**?\n\n"

            "**METHODS:**\n"
            "- What **operations** can the class perform?\n"
            "- Which methods are **public** (+), **private** (-), **protected** (#)?\n"
            "- What are the **parameters** and **return types**?\n"
            "- Which methods are **constructors**?\n"
            "- Which methods implement **business rules**?\n\n"

            "**STEP 4: RELATIONSHIP ANALYSIS**\n"
            "Determine the relationships between classes:\n\n"

            "**ASSOCIATIONS:**\n"
            "- Which classes **collaborate** with each other?\n"
            "- What is the **cardinality** of the relationship (1..1, 1..*, *..*)?\n"
            "- Is the relationship **bidirectional** or **unidirectional**?\n"
            "- What are the **roles** in the relationship?\n\n"

            "**INHERITANCE (VERY IMPORTANT!):**\n"
            "- Which classes are **specializations** (children) of other, more general classes (parents)?\n"
            "- **Key Rule:** The inheritance relationship (`--|>`) MUST always lead from the child to the parent. Example: `class Transfer extends TransactionType` in code means `Transfer --|> TransactionType` in PlantUML. Never the other way around! Verify this direction carefully.\n"
            "- Are abstract classes needed to gather common features?\n\n"

            "**AGGREGATION/COMPOSITION:**\n"
            "- Which classes are **parts** of other classes?\n"
            "- Can parts exist **independently** (aggregation) or **not** (composition)?\n\n"

            "**IMPLEMENTATION:**\n"
            "- Which classes **implement** interfaces?\n"
            "- Which classes **use** other classes?\n\n"

            "**STEP 5: PlantUML DIAGRAM GENERATION**\n"
            "Generate complete PlantUML code with the following requirements:\n\n"

            "**TECHNICAL STRUCTURE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "title [Process Name] - Class Model\n\n"

            "' Entity Classes\n"
            "class ClassName {{\n"
            "    +publicAttribute: Type\n"
            "    -privateAttribute: Type\n"
            "    #protectedAttribute: Type\n"
            "    --\n"
            "    +ClassName(param: Type)\n"
            "    +publicMethod(): ReturnType\n"
            "    -privateMethod(param: Type): ReturnType\n"
            "    +{{static}} staticMethod(): Type\n"
            "    +{{abstract}} abstractMethod(): Type\n"
            "}}\n\n"

            "abstract class AbstractClass {{\n"
            "    #{{abstract}} abstractMethod(): Type\n"
            "}}\n\n"

            "interface IInterface {{\n"
            "    +interfaceMethod(): Type\n"
            "}}\n\n"

            "enum StatusEnum {{\n"
            "    VALUE1\n"
            "    VALUE2\n"
            "    VALUE3\n"
            "}}\n\n"

            "' Relationships\n"
            "Class1 ||--o{{ Class2 : \"contains\"\n"
            "Class1 --> Class3 : \"uses\"\n"
            "Class4 --|> AbstractClass : \"inherits\"\n"
            "Class5 ..|> IInterface : \"implements\"\n"
            "Class6 ..> Class7 : \"depends on\"\n"
            "@enduml\n"
            "```\n\n"

            "**PlantUML RELATIONSHIP TYPES:**\n"
            "- `-->` : Association/uses\n"
            "- `--` : Bidirectional association\n"
            "- `--|>` : Inheritance (extends) (Remember: Always from CHILD to PARENT!)\n"
            "- `..|>` : Implementation (implements)\n"
            "- `||--` : Composition (part-whole, strong)\n"
            "- `o--` : Aggregation (part-whole, weak)\n"
            "- `..>` : Dependency\n"
            "- `*--` : Composition with cardinality\n\n"

            "**CARDINALITY:**\n"
            "- `\"1\"` : exactly one\n"
            "- `\"0..1\"` : zero or one\n"
            "- `\"1..*\"` : one or more\n"
            "- `\"*\"` : zero or more\n"
            "- `\"n\"` : exactly n\n\n"

            "**ACCESS MODIFIERS:**\n"
            "- `+` : public\n"
            "- `-` : private\n"
            "- `#` : protected\n"
            "- `~` : package\n\n"

            "**METHOD MODIFIERS:**\n"
            "- `{{static}}` : static method\n"
            "- `{{abstract}}` : abstract method\n"
            "- `{{final}}` : final method\n\n"

            "**GROUPING AND ORGANIZATION:**\n"
            "```plantuml\n"
            "package \"Domain Model\" {{\n"
            "    class DomainClass1\n"
            "    class DomainClass2\n"
            "}}\n\n"

            "package \"Services\" {{\n"
            "    class ServiceClass1\n"
            "    class ServiceClass2\n"
            "}}\n\n"

            "package \"Value Objects\" {{\n"
            "    class ValueObject1\n"
            "    enum StatusEnum\n"
            "}}\n"
            "```\n\n"

            "**NAMING CONVENTIONS:**\n"
            "- Class names: **PascalCase** (OrderService, CustomerData)\n"
            "- Attribute names: **camelCase** (firstName, orderDate)\n"
            "- Method names: **camelCase** (calculateTotal, validateData)\n"
            "- Constant names: **UPPER_CASE** (MAX_ITEMS, DEFAULT_STATUS)\n"
            "- Interfaces: prefix **I** (IPaymentProcessor, IOrderValidator)\n"
            "- Abstract classes: prefix **Abstract** (AbstractProcessor)\n\n"

            "**BEST PRACTICES:**\n"
            "- Separate attributes from methods with a `--` line\n"
            "- Group related classes into packages\n"
            "- Use comments (') to describe complex relationships\n"
            "- Specify cardinality for all associations\n"
            "- Add labels to relationships describing their meaning\n"
            "- Place enumerations close to the classes that use them\n\n"

            "**FINAL RESULT:**\n"
            "Provide complete, working PlantUML code that:\n"
            "1. Models all relevant objects from the business process\n"
            "2. Contains correct attributes and methods derived from the analysis\n"
            "3. Shows all relevant relationships between classes\n"
            "4. Is divided into logical packages/modules\n"
            "5. Contains comments explaining the process→class mapping\n"
            "6. Is ready to be used as a basis for implementation\n"
            "7. Reflects actual business rules in the code structure"
        ),
        "allowed_diagram_types": ["class"],
        "type": "PlantUML"
    },
    "Component Diagram - C4 Notation": {
        "template": (
            "As an experienced PlantUML coder and system architect, generate a C4 Component diagram in PlantUML for:\n{process_description}\n"
            "with the following requirements:\n\n"

            "**C4 COMPONENT TECHNICAL REQUIREMENTS:**\n"
            "1. **INCLUDES:** Use ONLY:\n"
            "   - `!include <C4/C4_Component>`\n"
            "   - Optionally `!include <C4/C4_Container>` if showing container context\n\n"

            "2. **AVAILABLE MACROS:**\n"
            "   - `Component(alias, \"Name\", \"Technology\", \"Functionality Description\")`\n"
            "   - `ComponentDb(alias, \"DB Name\", \"DB Type\", \"Data Description\")`\n"
            "   - `ComponentQueue(alias, \"Queue Name\", \"Technology\", \"Queue Description\")`\n"
            "   - `Container()` - ONLY for context, not as primary elements\n\n"

            "3. **DIAGRAM STRUCTURE:**\n"
            "   - Start: `@startuml`\n"
            "   - Include: `!include <C4/C4_Component>`\n"
            "   - Title: `title [System] - Component Diagram (C4 Level 3)`\n"
            "   - Optional container context: `Container_Boundary(container, \"Container\")`\n"
            "   - All component definitions\n"
            "   - Relationships between components\n"
            "   - End: `@enduml`\n\n"

            "4. **LEVEL OF DETAIL:**\n"
            "   - Show components WITHIN a single container/system\n"
            "   - Each component = specific business responsibility\n"
            "   - DO NOT mix levels of abstraction (System vs Component)\n"
            "   - Focus on data flow and calls between components\n\n"

            "5. **RELATIONSHIPS:**\n"
            "   - `Rel(source, target, \"Label\", \"Protocol/Technology\")`\n"
            "   - `Rel_Back()`, `Rel_Neighbor()` for better layout\n"
            "   - Always describe WHAT the communication is (API call, event, data flow)\n\n"

            "6. **NAMING CONVENTIONS:**\n"
            "   - Consistent language (Polish OR English)\n"
            "   - Component names = nouns describing function\n"
            "   - Aliases = short, no spaces, snake_case or camelCase\n\n"

            "7. **EXAMPLE OF CORRECT STRUCTURE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "!include <C4/C4_Component>\n"
            "title Order System - Components (C4 Level 3)\n\n"

            "Container_Boundary(api_container, \"API Container\") {{\n"
            "    Component(order_controller, \"Order Controller\", \"Spring MVC\", \"Handles HTTP requests for orders\")\n"
            "    Component(order_service, \"Order Service\", \"Spring Bean\", \"Order business logic\")\n"
            "    Component(payment_service, \"Payment Service\", \"Spring Bean\", \"Payment processing\")\n"
            "    Component(notification_service, \"Notification Service\", \"Spring Bean\", \"Sends notifications\")\n"
            "    ComponentDb(order_db, \"Orders Database\", \"PostgreSQL\", \"Stores order data\")\n"
            "    ComponentQueue(order_queue, \"Order Events\", \"RabbitMQ\", \"Order events queue\")\n"
            "}}\n\n"

            "Rel(order_controller, order_service, \"Invokes\", \"Method call\")\n"
            "Rel(order_service, payment_service, \"Processes payment\", \"Method call\")\n"
            "Rel(order_service, order_db, \"Saves order\", \"SQL\")\n"
            "Rel(order_service, order_queue, \"Publishes event\", \"AMQP\")\n"
            "Rel(notification_service, order_queue, \"Listens for events\", \"AMQP\")\n"
            "@enduml\n"
            "```\n\n"

            "8. **FORBIDDEN PRACTICES:**\n"
            "   - ❌ Mixing macros from different C4 levels\n"
            "   - ❌ Using `System()` in a component diagram\n"
            "   - ❌ Showing components from different containers without context\n"
            "   - ❌ Vague names like \"Service1\", \"Database\"\n"
            "   - ❌ Relationships without communication technology descriptions\n\n"

            "**RESULT:** Generate complete, working PlantUML code depicting components within a system/container according to C4 model Level 3."
        ),
        "allowed_diagram_types": ["component"],
        "type": "PlantUML"
    },
    "Component Diagram - Basic Notation": {
        "template": (
            "Based on the business process description: {process_description}\n\n"

            "**STEP 1: BUSINESS PROCESS ANALYSIS**\n"
            "Analyze the described process and identify:\n"
            "- Who participates in the process (actors, roles)?\n"
            "- What data is processed, stored, transferred?\n"
            "- What decisions are made and based on what?\n"
            "- What external systems are required?\n"
            "- What notifications/communication are needed?\n"
            "- What documents/reports are generated?\n\n"

            "**STEP 2: SYSTEM COMPONENT IDENTIFICATION**\n"
            "Based on the analysis, determine which IT components are needed:\n\n"

            "**A) USER INTERFACE LAYER:**\n"
            "- Is a web application needed?\n"
            "- Is an API needed for other systems?\n"
            "- Is an administration panel needed?\n"
            "- Are mobile interfaces needed?\n\n"

            "**B) BUSINESS LOGIC LAYER:**\n"
            "- What business services handle the main functions of the process?\n"
            "- Are components needed for data validation?\n"
            "- Are components needed for calculations/algorithms?\n"
            "- Are components needed for flow orchestration?\n\n"

            "**C) DATA ACCESS LAYER:**\n"
            "- What databases are needed (transactional, analytical)?\n"
            "- Are repositories/DAOs needed?\n"
            "- Is caching needed?\n"
            "- Are ETL components needed?\n\n"

            "**D) INTEGRATION COMPONENTS:**\n"
            "- What external systems need to be integrated with?\n"
            "- Are queues/message brokers needed?\n"
            "- Are components needed for data synchronization?\n"
            "- Are adapters/connectors needed?\n\n"

            "**E) SUPPORT COMPONENTS:**\n"
            "- Are components needed for notifications (email, SMS)?\n"
            "- Are components needed for report generation?\n"
            "- Are components needed for logging/auditing?\n"
            "- Are components needed for file management?\n\n"

            "**STEP 3: PlantUML DIAGRAM GENERATION**\n"
            "Generate complete PlantUML code in basic notation with the following requirements:\n\n"

            "**TECHNICAL STRUCTURE:**\n"
            "1. **Start:** `@startuml`\n"
            "2. **Title:** `title [Process Name] - System Architecture`\n"
            "3. **Define all elements before relationships**\n"
            "4. **End:** `@enduml`\n\n"

            "**ELEMENTS TO USE:**\n"
            "- `actor \"Name\" as alias` - users/roles\n"
            "- `component \"Name\" <<stereotype>> as alias` - business components\n"
            "- `database \"Name\" as alias` - databases\n"
            "- `queue \"Name\" as alias` - queues/brokers\n"
            "- `file \"Name\" as alias` - storage/files\n"
            "- `cloud \"Name\" as alias` - external systems\n"
            "- `interface \"Name\" as alias` - interfaces\n\n"

            "**GROUPING:**\n"
            "- `package \"UI Layer\" {{ }}` - UI layer\n"
            "- `package \"Business Layer\" {{ }}` - business logic\n"
            "- `package \"Data Layer\" {{ }}` - data access\n"
            "- `package \"Integration Layer\" {{ }}` - integrations\n"
            "- `frame \"[System Name]\" {{ }}` - system boundaries\n\n"

            "**STEREOTYPES:**\n"
            "- `<<controller>>` - Web/API controllers\n"
            "- `<<service>>` - business services\n"
            "- `<<repository>>` - data access\n"
            "- `<<facade>>` - integration facades\n"
            "- `<<utility>>` - support components\n"
            "- `<<gateway>>` - API gateways\n\n"

            "**RELATIONSHIPS WITH DESCRIPTIONS:**\n"
            "- `-->` with labels like: \"HTTP API\", \"SQL Query\", \"Message\", \"File Access\"\n"
            "- Always describe the communication protocol/technology\n"
            "- Group similar relationships for readability\n\n"

            "**EXAMPLE STRUCTURE:**\n"
            "```plantuml\n"
            "@startuml\n"
            "title [Process Name] - System Architecture\n\n"

            "' Actors from the business process\n"
            "actor \"[Role1]\" as actor1\n"
            "actor \"[Role2]\" as actor2\n\n"

            "' External systems identified in the process\n"
            "cloud \"[External System]\" as ext_system\n\n"

            "frame \"[Process Name] System\" {{\n"
            "    package \"UI Layer\" {{\n"
            "        component \"[Process] Web App\" <<controller>> as web_app\n"
            "        component \"[Process] API\" <<gateway>> as api\n"
            "    }}\n\n"

            "    package \"Business Layer\" {{\n"
            "        component \"[Process] Service\" <<service>> as main_service\n"
            "        component \"[Function] Service\" <<service>> as func_service\n"
            "        interface \"I[Process]Service\" as iservice\n"
            "    }}\n\n"

            "    package \"Data Layer\" {{\n"
            "        component \"[Entity] Repository\" <<repository>> as repo\n"
            "        database \"[Process] Database\" as db\n"
            "    }}\n\n"

            "    package \"Integration Layer\" {{\n"
            "        component \"[External] Adapter\" <<facade>> as adapter\n"
            "        queue \"[Process] Events\" as queue\n"
            "    }}\n"
            "}}\n\n"

            "' Relationships derived from the process flow\n"
            "actor1 --> web_app : \"Initiates process\"\n"
            "web_app --> iservice : \"Invokes logic\"\n"
            "main_service ..|> iservice : \"implements\"\n"
            "main_service --> repo : \"Retrieves/saves data\"\n"
            "repo --> db : \"SQL\"\n"
            "main_service --> adapter : \"External integration\"\n"
            "adapter --> ext_system : \"API call\"\n"
            "@enduml\n"
            "```\n\n"

            "**NAMING CONVENTIONS:**\n"
            "- Component names should reflect functions from the business process\n"
            "- Use functional names, not technical ones (\"Order Service\" instead of \"Service1\")\n"
            "- Aliases short, no spaces (order_service, payment_api)\n"
            "- Consistent language (Polish or English)\n\n"

            "**FINAL RESULT:**\n"
            "Provide complete, working PlantUML code that:\n"
            "1. Reflects all aspects of the business process in the form of IT components\n"
            "2. Shows the logical system architecture needed to handle the process\n"
            "3. Includes all necessary integrations and data flows\n"
            "4. Is ready to use without modification\n"
            "5. Contains comments explaining the process→components mapping"
        ),
        "allowed_diagram_types": ["component"],
        "type": "PlantUML"
    },
    "BPMN - basic": {
        "template": (
            "**As an experienced business analyst and process architect with 10 years of experience in BPMN 2.0 notation, prepare a complete business process diagram according to the description:**\n\n"
            "{process_description}\n\n"
            "**PROCESS ANALYSIS:**\n"
            "1. Identify all process participants\n"
            "2. Determine the sequence of steps and decision points\n"
            "3. Capture interactions between participants\n"
            "4. Include exception and error scenarios\n\n"
            "**TECHNICAL REQUIREMENTS:**\n"
            "- Format: Complete, valid BPMN 2.0 XML code\n"
            "- Compatibility: Ready for direct import into Camunda Modeler 5.x\n"
            "- Structure: All required XML sections (definitions, process, collaboration, bpmndi)\n"
            "- Namespaces: Use full xmlns definitions for BPMN 2.0\n\n"
            "**DIAGRAM ARCHITECTURE:**\n"
            "- **Pools**: Separate pools for each main participant\n"
            "- **Lanes**: Subdivisions within pools for different roles/systems\n"
            "- **Message Flows**: Communication between participants\n"
            "- **Sequence Flows**: Flow within the process\n\n"
            "**ELEMENT TYPES:**\n"
            "- Start/End Events: Appropriate types (None, Message, Timer, Error)\n"
            "- Tasks: User Task, Service Task, Send Task, Receive Task, Script Task\n"
            "- Gateways: Exclusive, Inclusive, Parallel, Event-based\n"
            "- Intermediate Events: Message, Timer, Error, Escalation\n\n"
            "**STANDARD PARTICIPANTS (adapt to context):**\n"
            "1. Client/User (Pool: \"Client\")\n"
            "2. Organization/Department (Pool: \"[Organization Name]\")\n"
            "3. External System (Pool: \"System [Name]\")\n"
            "4. Partner/Supplier (Pool: \"[Partner Name]\")\n\n"
            "**ERROR HANDLING:**\n"
            "- Error Events for critical errors\n"
            "- Escalation Events for escalation\n"
            "- Compensation Events where required\n"
            "- Timeout Events for time limits\n\n"
            "**QUALITY REQUIREMENTS:**\n"
            "- All elements with unique IDs (format: Element_001, Task_002, etc.)\n"
            "- Names in Polish, legible and descriptive\n"
            "- Correct attributes for each element\n"
            "- Complete DI information (positions, sizes, colors)\n\n"
            "**XML SECTIONS - REQUIRED:**\n"
            "```xml\n"
            "<definitions xmlns=\"[http://www.omg.org/spec/BPMN/20100524/MODEL](http://www.omg.org/spec/BPMN/20100524/MODEL)\"\n"
            "             xmlns:bpmndi=\"[http://www.omg.org/spec/BPMN/20100524/DI](http://www.omg.org/spec/BPMN/20100524/DI)\"\n"
            "             xmlns:omgdc=\"[http://www.omg.org/spec/DD/20100524/DC](http://www.omg.org/spec/DD/20100524/DC)\"\n"
            "             xmlns:omgdi=\"[http://www.omg.org/spec/DD/20100524/DI](http://www.omg.org/spec/DD/20100524/DI)\">\n"
            "  <collaboration id=\"Collaboration_1\">\n"
            "    <participant id=\"Participant_1\"/>\n"
            "  </collaboration>\n"
            "  <process id=\"Process_1\">\n"
            "    <laneSet id=\"LaneSet_1\">\n"
            "      <lane id=\"Lane_1\"/>\n"
            "    </laneSet>\n"
            "  </process>\n"
            "  <bpmndi:BPMNDiagram id=\"BPMNDiagram_1\">\n"
            "    <bpmndi:BPMNPlane id=\"BPMNPlane_1\">\n"
            "    </bpmndi:BPMNPlane>\n"
            "  </bpmndi:BPMNDiagram>\n"
            "</definitions>\n"
            "```\n\n"
            "**RESULT:** Provide ONLY complete, working BPMN 2.0 XML code without additional comments and a full XML structure compatible with Camunda Modeler 5.x.\n"
        ),
        "allowed_diagram_types": ["BPMN"],
        "type": "XML"
    },
    "BPMN - advanced": {
        "template": (
            "**As a senior business process architect with BPMN 2.0 certification, analyze the process and create a professional diagram:**\n\n"
            "{process_description}\n\n"
            "**DEEP ANALYSIS:**\n"
            "1. **Stakeholder Mapping**: Identify all stakeholders\n"
            "2. **Process Decomposition**: Break down into sub-processes where sensible\n"
            "3. **Exception Handling**: Include all exception scenarios\n"
            "4. **Compliance**: Add control and audit points\n\n"
            "**ENTERPRISE REQUIREMENTS:**\n"
            "- **Governance**: Add process owner and RACI roles\n"
            "- **Monitoring**: Include KPIs and measurement points\n"
            "- **Integration**: Define integration points with other systems\n"
            "- **Security**: Add security and authorization points\n\n"
            "**ADVANCED ELEMENTS:**\n"
            "- **Sub-processes**: For complex operations\n"
            "- **Call Activities**: For reusable processes\n"
            "- **Event Sub-processes**: For exception handling\n"
            "- **Compensation**: For transactions requiring rollback\n\n"
            "**QUALITY GATES:**\n"
            "- Syntactic correctness validation\n"
            "- Flow completeness check\n"
            "- Business logic verification\n"
            "- Import test into Camunda Modeler\n\n"
            "**OUTPUT:** Complete, enterprise-ready BPMN 2.0 XML"
        ),
        "allowed_diagram_types": ["BPMN"],
        "type": "XML"
    },
    "BPMN - banking domain": {
        "template": (
            "**As a {domain} industry expert with 15 years of experience in BPMN processes, prepare a diagram compliant with sector best practices:**\n\n"
            "{process_description}\n\n"
            "**DOMAIN EXPERTISE:**\n"
            "- Account for specific industry requirements\n"
            "- Apply standard process patterns for {domain}\n"
            "- Maintain compliance with sector regulations\n"
            "- Use standard industry terminology\n\n"
            "**INDUSTRY PATTERNS:**\n"
            "- Financial: AML, KYC, PCI DSS, GDPR\n"
            "- Medical: HIPAA, FDA, GxP\n"
            "- Manufacturing: ISO 9001, Lean, Six Sigma\n"
            "- E-commerce: PCI DSS, GDPR, Consumer Protection\n\n"
            "**COMPLIANCE CHECKPOINTS:**\n"
            "- Regulatory control points\n"
            "- Audit documentation\n"
            "- Audit trails\n"
            "- Approvals and escalations\n\n"
            "**OUTPUT:** Industry-specific BPMN 2.0 XML"
        ),
        "allowed_diagram_types": ["BPMN"],
        "type": "XML",
        "parameters": ["domain"]
    },
    "PlantUML Code Verification": {
        "template": (
            "**PLANTUML CODE VERIFICATION AND AUTO-CORRECTION**\n\n"
            "**Diagram type:** {diagram_type}\n"
            "**Task:** Analyze the code, identify errors, and provide a corrected version\n\n"
            "**CODE TO ANALYZE:**\n"
            "```plantuml\n"
            "{plantuml_code}\n"
            "```\n\n"
            "**VERIFICATION AND FIXING INSTRUCTIONS:**\n\n"
            "**1. SYNTAX ANALYSIS:**\n"
            "   □ Check @startuml/@enduml tags\n"
            "   □ Validate brackets, quotation marks, semicolons\n"
            "   □ Evaluate structure and indentation\n"
            "   □ Identify syntax errors\n\n"
            "**2. ELEMENT VALIDATION ({diagram_type}):**\n"
            "   □ Check diagram-type-specific elements\n"
            "   □ Validate keywords and commands\n"
            "   □ Assess completeness of required components\n"
            "   □ Ensure there are no lines starting with the '!' character\n"
            "   □ Check naming and conventions\n\n"
            "**3. RELATIONSHIP CHECK:**\n"
            "   □ Verify arrows and connectors\n"
            "   □ Ensure all references are defined\n"
            "   □ Assess logical consistency of connections\n"
            "   □ Remove unnecessary or incorrect relationships\n\n"
            "**4. STYLE OPTIMIZATION:**\n"
            "   □ Improve colors and styles\n"
            "   □ Enhance code readability\n"
            "   □ Remove duplicates\n"
            "   □ Apply best practices\n\n"
            "**REQUIRED RESPONSE FORMAT:**\n\n"
            "**VERIFICATION STATUS:**\n"
            "[Select one:]\n"
            "✅ **VALID** – the code requires no changes\n"
            "⚠️ **FIXED** – errors were found and corrected\n"
            "❌ **CRITICAL** – severe issues that need attention\n\n"
            "**IDENTIFIED ISSUES:**\n"
            "[List of errors with line numbers, only if present:]\n"
            "• **Line X:** [issue description] → [how it was fixed]\n"
            "• **Line Y:** [issue description] → [how it was fixed]\n\n"
            "**CORRECTED PLANTUML CODE:**\n"
            "```plantuml\n"
            "[Insert the corrected code here — if the original was valid, copy it unchanged]\n"
            "```\n\n"
            "**SUMMARY OF CHANGES:**\n"
            "[Describe the changes made and why they were necessary. If no changes, write 'No changes – the code was valid']\n\n"
            "**ADDITIONAL RECOMMENDATIONS:**\n"
            "[Optional improvement suggestions or warnings]\n\n"
            "**NOTES:**\n"
            "- Preserve the original logic and structure of the diagram\n"
            "- Only correct syntactic and technical errors\n"
            "- Add comments to complex parts if needed\n"
            "- Ensure the code renders correctly in PlantUML\n"
            "- Ensure there are no comments in the code — remove all lines starting with '!'\n"
        ),
        "allowed_diagram_types": "all",
        "type": "Verification"
    },
    "Process Description Verification": {
        "template": (
            "**Verification of the process description for diagram type: {diagram_type}**\n\n"
            "**Process description to verify:**\n"
            "{process_description}\n\n"
            "**Conduct a detailed analysis according to the requirements for diagram type {diagram_type}:**\n\n"

            "**1. GENERAL ANALYSIS:**\n"
            "- Does the process have a clearly defined start and end point?\n"
            "- Are all steps logically connected?\n"
            "- Are any key elements of the process missing?\n"
            "- Is the description unambiguous and understandable?\n\n"

            "**2. DIAGRAM-SPECIFIC REQUIREMENTS FOR {diagram_type}:**\n"
            "{diagram_specific_requirements}\n\n"

            "**3. COMPLETENESS VERIFICATION:**\n"
            "- Check whether all necessary roles/actors are identified\n"
            "- Verify whether all decisions and branching points are described\n"
            "- Ensure that all exceptions and alternative paths are included\n\n"

            "**4. VERIFICATION RESULT:**\n"
            "Provide the result in the following format:\n"
            "- **STATUS:** [VALID/REQUIRES_CHANGES/INCOMPLETE]\n"
            "- **MAIN ISSUES:** [list of main issues or 'None']\n"
            "- **SUGGESTED CHANGES:** [specific suggestions or 'None']\n"
            "- **MISSING ELEMENTS:** [list of missing elements or 'None']\n"
            "- **RECOMMENDATIONS:** [additional suggestions for improving the diagram]\n\n"

            "**5. PROPOSAL:**\n"
            "[prepare how the corrected description should look so it can be sent to the model]\n\n"

            "If the description is fully correct and complete, write: '✅ THE DESCRIPTION IS VALID AND COMPLETE FOR DIAGRAM TYPE {diagram_type}'"
        ),
        "allowed_diagram_types": "all",
        "type": "Validation"
    }


}
c4_component_requirements = (
    "- Does it use correct includes for component level?\n"
    "- Do all components belong to the same container/system?\n"
    "- Does each component have a clearly defined responsibility?\n"
    "- Do relationships describe specific types of communication?\n"
    "- Does the diagram avoid mixing C4 abstraction levels?\n"
    "- Are component names functional (not technical)?\n"
)

usecase_requirements = (
    "- Are all actors (primary and secondary) identified?\n"
    "- Are use cases atomic and focused on a single goal?\n"
    "- Are extend and include relationships correctly described?\n"
    "- Are preconditions and postconditions defined?\n"
    "- Are alternative scenarios included?\n"
)

sequence_requirements = (
    "- Are all objects/actors participating in the process identified?\n"
    "- Is the sequence of interactions logical and complete?\n"
    "- Are all messages between objects described?\n"
    "- Are object lifelines clearly defined?\n"
    "- Are all conditions and loops included?\n"
)

bpmn_requirements = (
    "- Are all pools and lanes defined?\n"
    "- Are start and end events clearly defined?\n"
    "- Do all gateways have defined conditions?\n"
    "- Are inter-organizational processes correctly described?\n"
    "- Do all tasks have assigned performers?\n"
)

flowchart_requirements = (
    "- Do all decision points have clearly defined conditions (yes/no)?\n"
    "- Do all paths lead to a logical conclusion?\n"
    "- Are parallel processes clearly marked?\n"
    "- Are all loops and iterations described with termination conditions?\n"
)

class_requirements = (
    "- Do all classes have clearly defined attributes and methods?\n"
    "- Are relationships between classes (inheritance, associations) correctly defined?\n"
    "- Does the diagram contain all relevant classes and interfaces?\n"
    "- Are class names consistent and unambiguous?\n"
)

component_requirements = (
    "- Are all components clearly defined and have unique names?\n"
    "- Are relationships between components correctly described?\n"
    "- Does the diagram contain all relevant system components?\n"
    "- Is consistent notation used for components and interfaces?\n"
)

activity_requirements = (
    "- Are all activities clearly defined?\n"
    "- Does the diagram contain all relevant activities and decisions?\n"
    "- Are alternative paths and termination conditions correctly described?\n"
    "- Is the diagram readable and logically organized?\n"
)

deployment_requirements = (
    "- Are all deployment elements (e.g., servers, databases) clearly defined?\n"
    "- Are relationships between deployment elements correctly described?\n"
    "- Does the diagram contain all relevant infrastructure elements?\n"
    "- Is consistent notation used for deployment elements and artifacts?\n"
)

object_requirements = (
    "- Are all objects clearly defined and have unique names?\n"
    "- Are relationships between objects correctly described?\n"
    "- Does the diagram contain all relevant objects and their attributes?\n"
    "- Is consistent notation used for objects and their relationships?\n"
)

state_requirements = (
    "- Are all states clearly defined?\n"
    "- Are transitions between states correctly described?\n"
    "- Does the diagram contain all relevant states and their relationships?\n"
    "- Is consistent notation used for states and transitions?\n"
)

def get_diagram_specific_requirements(diagram_type):
    requirements_map = {
        "flowchart": flowchart_requirements,
        "bpmn": bpmn_requirements,
        "sequence": sequence_requirements,
        "usecase": usecase_requirements,
        "class": class_requirements,
        "component": component_requirements,
        "activity": activity_requirements,
        "deployment": deployment_requirements,
        "object": object_requirements,  
        "state": state_requirements,
        # dodaj więcej typów według potrzeb
    }