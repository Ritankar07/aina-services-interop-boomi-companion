# Boomi Component XML Guide
## Correct XML Structure for Every Component Type

**Source:** Adapted from OfficialBoomi/boomi-integration component reference documentation.
**Rule:** Read BOOMI_THINKING.md first. Then read the section for the specific component type you are creating.

---

## General Rules (Apply to ALL Components)

1. **`componentId`** — empty string `""` for CREATE operations. Platform generates a real GUID on push.
2. **`folderId`** — MUST be present and non-empty. Never push without a real folder GUID.
3. **`version`** — always `"-1"` for CREATE, incremented by platform on each push.
4. **Encrypted fields** — leave as empty string `""`. Configure via Environment Extensions in UI.
5. **NEVER** use PLACEHOLDER values, `${ENV_VAR}`, or made-up GUIDs in XML that will be pushed.

---

## Process Component

**Platform type identifier:** `process`
**Local folder:** `active-development/process/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="API_GET_Policy"
    type="process"
    version="-1">
  <bns:object>
    <bns:ProcessDefinition
        allowSimultaneous="false"
        enableUserLog="false"
        processLogOnErrorOnly="false"
        purgeDataImmediately="false"
        updateRunDates="true"
        workload="general">
      <bns:shapes>
        <!-- Steps go here — every step MUST have <dragpoints> -->
      </bns:shapes>
    </bns:ProcessDefinition>
  </bns:object>
</bns:Component>
```

**allowSimultaneous:** Set `true` for Trading Partner Start and listener processes.
**processLogOnErrorOnly:** Set `true` for high-volume production processes.

---

## JSON Profile Component

**Platform type identifier:** `profile.json`
**Local folder:** `active-development/profile.json/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="Policy_Request_JSON"
    type="profile.json"
    version="-1">
  <bns:object>
    <bns:JSONProfile>
      <bns:elements>
        <bns:element maxOccurs="1" minOccurs="0" name="policyId" type="String"/>
        <bns:element maxOccurs="1" minOccurs="0" name="effectiveDate" type="String"/>
        <!-- Add all fields of the JSON structure here -->
      </bns:elements>
    </bns:JSONProfile>
  </bns:object>
</bns:Component>
```

**Field types:** `String`, `Number`, `Boolean`, `DateTime`
**For arrays:** Use `maxOccurs="unbounded"` and add child `<bns:elements>` inside the element.

---

## XML Profile Component

**Platform type identifier:** `profile.xml`
**Local folder:** `active-development/profile.xml/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="Policy_Request_XML"
    type="profile.xml"
    version="-1">
  <bns:object>
    <bns:XMLProfile>
      <bns:XMLFlavor>
        <bns:CustomStandardFlavor/>
      </bns:XMLFlavor>
      <bns:elements>
        <bns:element maxOccurs="1" minOccurs="0" name="PolicyRequest" type="element">
          <bns:elements>
            <bns:element maxOccurs="1" minOccurs="0" name="policyId" type="element"/>
          </bns:elements>
        </bns:element>
      </bns:elements>
    </bns:XMLProfile>
  </bns:object>
</bns:Component>
```

**Critical:** `<bns:XMLFlavor><bns:CustomStandardFlavor/></bns:XMLFlavor>` is REQUIRED. Omitting it causes the profile to fail validation on PUT/POST operations.

---

## REST Connection Component

**Platform type identifier:** `connector-settings`
**Local folder:** `active-development/connector-settings/`
**connectorType:** `officialboomi-X3979C-rest-prod`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="CONN_Guidewire"
    type="connector-settings"
    version="-1">
  <bns:object>
    <bns:ConnectorSettings connectorType="officialboomi-X3979C-rest-prod">
      <bns:settings>
        <!-- Base URL: configure via Environment Extension after push -->
        <bns:setting id="url" value=""/>
        <!-- Auth type: none, basic, apikey, oauth2 -->
        <bns:setting id="authenticationType" value="none"/>
        <!-- Leave credential fields empty — configure via Environment Extensions -->
        <bns:setting id="username" value=""/>
        <bns:setting id="password" encryptedValue=""/>
      </bns:settings>
    </bns:ConnectorSettings>
  </bns:object>
</bns:Component>
```

**NEVER** use `connectorType="http"` unless the user explicitly requests HTTP Client.

---

## REST Operation Component

**Platform type identifier:** `connector-action`
**Local folder:** `active-development/connector-action/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="GET_Policy"
    type="connector-action"
    version="-1">
  <bns:object>
    <bns:ConnectorAction connectorType="officialboomi-X3979C-rest-prod">
      <bns:settings>
        <!-- HTTP method: GET, POST, PUT, DELETE, PATCH -->
        <bns:setting id="httpMethod" value="GET"/>
        <!-- Resource path — can include {pathParam} placeholders -->
        <bns:setting id="resourcePath" value="/api/policies/{policyId}"/>
        <!-- Request profile — use GUID from the pushed profile component -->
        <bns:setting id="requestProfile" value="ACTUAL_REQUEST_PROFILE_GUID"/>
        <!-- Response profile — use GUID from the pushed profile component -->
        <bns:setting id="responseProfile" value="ACTUAL_RESPONSE_PROFILE_GUID"/>
      </bns:settings>
    </bns:ConnectorAction>
  </bns:object>
</bns:Component>
```

---

## Map Component

**Platform type identifier:** `transform.map`
**Local folder:** `active-development/transform.map/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="MAP_Request_TO_GWPolicy"
    type="transform.map"
    version="-1">
  <bns:object>
    <bns:MapDefinition>
      <!-- Source profile GUID — from pushed profile component -->
      <bns:fromProfile id="ACTUAL_SOURCE_PROFILE_GUID"/>
      <!-- Target profile GUID — from pushed profile component -->
      <bns:toProfile id="ACTUAL_TARGET_PROFILE_GUID"/>
      <bns:maps>
        <!-- Field-to-field mapping -->
        <bns:map>
          <bns:fromElement xpath="policyId"/>
          <bns:toElement xpath="policyNumber"/>
        </bns:map>
        <!-- More mappings... -->
      </bns:maps>
    </bns:MapDefinition>
  </bns:object>
</bns:Component>
```

---

## Document Cache Component

**Platform type identifier:** `documentcache`
**Local folder:** `active-development/documentcache/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="CACHE_AccessToken"
    type="documentcache"
    version="-1">
  <bns:object>
    <bns:DocumentCache>
      <bns:indexes>
        <bns:index name="tokenKey">
          <bns:keys>
            <bns:key profileFieldPath="tokenId"/>
          </bns:keys>
        </bns:index>
      </bns:indexes>
    </bns:DocumentCache>
  </bns:object>
</bns:Component>
```

**Cache scope:** Process lifetime only. Does not persist between executions. Node-local on Molecule.

---

## Cross Reference Table Component

**Platform type identifier:** `crossreference`
**Local folder:** `active-development/crossreference/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="XREF_ProductCode"
    type="crossreference"
    version="-1">
  <bns:object>
    <bns:CrossReferenceTable matchType="EXACT">
      <bns:inputs>
        <bns:input name="sourceCode"/>
      </bns:inputs>
      <bns:outputs>
        <bns:output name="targetCode"/>
      </bns:outputs>
      <bns:rows>
        <bns:row>
          <bns:input value="SRC_001"/>
          <bns:output value="TGT_001"/>
        </bns:row>
      </bns:rows>
    </bns:CrossReferenceTable>
  </bns:object>
</bns:Component>
```

**matchType:** `EXACT`, `WILDCARD`, or `REGEX`
**Behavior:** Case-insensitive, first-row-wins, empty string on no-match.

---

## Process Property Component

**Platform type identifier:** `processproperty`
**Local folder:** `active-development/processproperty/`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
    componentId=""
    folderId="ACTUAL_FOLDER_GUID"
    name="PP_API_Config"
    type="processproperty"
    version="-1">
  <bns:object>
    <bns:ProcessProperty>
      <bns:properties>
        <bns:property name="baseUrl" type="String" value=""/>
        <bns:property name="timeout" type="Number" value="30"/>
        <bns:property name="retryCount" type="Number" value="3"/>
      </bns:properties>
    </bns:ProcessProperty>
  </bns:object>
</bns:Component>
```

**Types:** `String`, `Number`, `Boolean`, `DateTime`, `Password`

---

## Step XML Reference (Inside Process)

### Start Step — API Service (WSS Listener)
```xml
<bns:step name="Start" shapetype="start" posX="48" posY="192">
  <dragpoints/>
  <bns:configuration>
    <bns:ProcessStart type="listener">
      <bns:connectorType>wss</bns:connectorType>
      <bns:operationId>ACTUAL_WSS_OPERATION_GUID</bns:operationId>
    </bns:ProcessStart>
  </bns:configuration>
</bns:step>
```

### Start Step — Schedule
```xml
<bns:step name="Start" shapetype="start" posX="48" posY="192">
  <dragpoints/>
  <bns:configuration>
    <bns:ProcessStart type="schedule">
      <bns:scheduleType>SCHEDULED</bns:scheduleType>
    </bns:ProcessStart>
  </bns:configuration>
</bns:step>
```

### REST Connector Step
```xml
<bns:step name="Get Policy" shapetype="connector" posX="192" posY="192">
  <dragpoints>
    <dragpoint fromStepId="start" toStepId="this-step-id"/>
  </dragpoints>
  <bns:configuration>
    <bns:ConnectorStep>
      <bns:connectorId>ACTUAL_CONNECTION_GUID</bns:connectorId>
      <bns:operationId>ACTUAL_OPERATION_GUID</bns:operationId>
    </bns:ConnectorStep>
  </bns:configuration>
</bns:step>
```

### Map Step
```xml
<bns:step name="Map Response" shapetype="map" posX="336" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
  <map mapId="ACTUAL_MAP_COMPONENT_GUID"/>
</bns:step>
```

### Message Step (with JSON body — use quote escaping)
```xml
<bns:step name="Build Request" shapetype="message" posX="192" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
  <bns:configuration>
    <bns:Message>
      <bns:bodyType>plaintext</bns:bodyType>
      <!-- Single-quote wrapping required for JSON bodies -->
      <content><![CDATA['{"policyId":"'{1}'"}']]></content>
      <bns:parameters>
        <bns:parameter id="1" valueType="process" name="policyId"/>
      </bns:parameters>
    </bns:Message>
  </bns:configuration>
</bns:step>
```

### Set Properties Step — DPP
```xml
<bns:step name="Set Policy ID" shapetype="documentproperties" posX="192" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
  <bns:configuration>
    <bns:SetProperties>
      <bns:properties>
        <bns:property name="policyId" valueType="process">
          <bns:value xpath="//policyId"/>
        </bns:property>
      </bns:properties>
    </bns:SetProperties>
  </bns:configuration>
</bns:step>
```

### Decision Step
```xml
<bns:step name="Check Status" shapetype="decision" posX="192" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
  <bns:configuration>
    <bns:Decision>
      <!-- operator: equals, notequals, lessthan, greaterthan -->
      <bns:operator>equals</bns:operator>
      <bns:leftValue valueType="process" name="status"/>
      <bns:rightValue valueType="static" value="ACTIVE"/>
    </bns:Decision>
  </bns:configuration>
</bns:step>
```

**Valid operators only:** `equals`, `notequals`, `lessthan`, `greaterthan`, `lessthanorequal`, `greaterthanorequal`
**Invalid (do not use):** `isempty`, `isnotempty`, `contains`
**Empty check:** Use `equals` with empty static value `value=""`

### Try/Catch Step
```xml
<bns:step name="Error Handler" shapetype="trycatch" posX="192" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
  <bns:configuration>
    <bns:TryCatch>
      <!-- Steps inside try block -->
    </bns:TryCatch>
  </bns:configuration>
</bns:step>
```

### Return Documents Step
```xml
<bns:step name="Return" shapetype="return" posX="480" posY="192">
  <dragpoints>
    <dragpoint fromStepId="previous-step" toStepId="this-step"/>
  </dragpoints>
</bns:step>
```

---

## Component Creation Checklist

Before generating any component XML:

- [ ] Read BOOMI_THINKING.md push-as-you-go rule
- [ ] Identify ALL components needed and their dependency order
- [ ] Confirm folder GUID is available (run boomi_folder.py if needed)
- [ ] Start with profiles — no other component can be created until profiles are pushed and GUIDs captured
- [ ] No PLACEHOLDER GUIDs — use only real GUIDs from pushed components
- [ ] No credential values in XML — empty string or Environment Extension
- [ ] Every step has `<dragpoints>`
- [ ] Message step with JSON body uses single-quote escaping
- [ ] Set Properties uses `shapetype="documentproperties"`
- [ ] Map step has only `<map mapId="guid"/>`, no children
- [ ] XML profiles include `<bns:XMLFlavor><bns:CustomStandardFlavor/></bns:XMLFlavor>`
