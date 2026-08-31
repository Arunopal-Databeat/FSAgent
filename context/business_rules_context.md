#### **Revenue Data (Actual/Backlog/Target/Plan)**

#### **-----------------------------------------**



Actual - Amount already invoiced to the client. From the ActualBacklog Table, everything up to and including last month

Backlog - Amount expected to be invoiced to the client. From the ActualBacklog Table, everything from the current month onward

Plan - Data you find in **financial\_mmplan (Mediamint), financial\_dbplantarget (Databeat) and financial\_tdplantarget (Taktical)** client level

Target - Data you find in **financial\_mmtargetportfolio (Mediamint), financial\_dbplantarget (Databeat) and financial\_tdplantarget (Taktical).** Out of these only mediamint has client level data of target. Databeat and Taktical has aggregated info monthwise. You've to look for "Target" row in Account/Client for databeat and taktical table respectively. 



On request from users, you should make sure if the specific user's email is in **authentication\_alloweduser**, if it is give them plan data. if not give them target data.

If the users in **authentication\_alloweduser** explicitly asks for target, then only give them the data for target. But users outside of that tables, even if they ask for Plan explicitly don't return those data's. They are not authorized to see those. 



In **financial\_mmplan, financial\_mmtargetportfolio, financial\_dbplantarget and financial\_tdplantarget,** you could find **is\_aggregate = true** row's in Client Name column reffered to "NC", which is basically the monthly data for New Clients it can be plan/target based on which sheet you're processing. You might think what about existing client, those data you can compute by getting the amount of client's which are already in the sheet, but not for Target for Databeat and Taktical cause it doesn't have Client level breakdown of Target like mentioned above.



Like in **financial\_mmplan:**

* "Board Plan NC" 



**financial\_mmtargetportfolio:**

* "NC Target"



**financial\_dbplantarget:**

* "Board Plan NC"
* "Target"



**financial\_tdplantarget:**

* "Target"



Taktical doesn't have New Client Board Plan



Also Databeat and Taktical doesn't have segregation of New client and Existing Client for Target



**Shared Fields**

\-------------

Apr26 ..Oct26... Mar27 (IntegerField) - This financial year data. there will be total 12 columns (for 12 months)

snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last ingestion before today. The response to the question should be based on latest snapshot date

Client Name (CharField) - Name of the client. the column which we use to map to financial\_clientportfoliomapping table's Client Name field. All the tables doesn't have the same column name's it does vary.

is\_aggregate (BooleanField) - Tells if the row is aggregated amount

Total (IntegerField) - Total Amount of the client/aggregated row



**financial\_mmactualbacklog (Shared Fields)**

\-------------------------

Description: Revenue from Mediamint (MM) Clients which are Actual and Backlog



**financial\_dbactualbacklog (Shared Fields)**

\-------------------------

Description: Revenue from Databeat (DB) Clients which are Actual and Backlog



**financial\_takticalactualbacklog (Shared Fields)**

\-------------------------------

Description: Revenue from Taktical (TD) Clients which are Actual and Backlog



**financial\_mmplan (Shared Fields)**

\----------------

Description: Board Plan of Mediamint (MM) Clients



**financial\_mmtargetportfolio (Shared Fields)**

\---------------------------

Description: Target of Mediamint (MM) Clients



**financial\_dbplantarget (Shared Fields)**

\----------------------

Description: Board Plan of Databeat (DB) Clients. Target doesn't have client level breakdown. Though it has monthly Target of all clients



**financial\_tdplantarget (Shared Fields)**

\----------------------

Description: Board Plan of Taktical (TD) Clients. Target doesn't have client level breakdown. Though it has monthly Target of all clients



**financial\_clientportfoliomapping**

\-------------------------------

Description: Central Mapping sheet used to map salesforce opportunities data with Each Accounts Revenue (Actual/Backlog/Plan/Target). We even use this for Access Control, where we control which Client Partners/Portfolio Lead can access their assigned accounts data.



Columns:

\-------

\- snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last ingestion before today. The response to the question should be based on latest snapshot date

\- Client Name (CharField) - Name of the client. This is what the "Actual/Backlog/Plan/Target" Table's Client Name column map with join client's between these tables.

\- Portfolio Lead (CharField) - Name of Portfolio Lead assigned to the account

\- Client Partner (CharField) - Name of Client Partner assigned to the account

\- Client Entity (CharField) - Parent company name of the account, One of the dimension which we use to Map Actual/Backlog/Target/Plan with Salesforce opportunities data

\- MM ID (CharField) - Unique Identifier of the client, One of the dimension which we use to Map Actual/Backlog/Target/Plan with Salesforce opportunities data

\- Operational Group (CharField) - The Entity the client comes under (Mediamint, Databeat, Taktical)

\- Portfolio Lead Email (EmailField) - Email of the Portfolio Lead

\- Client Partner Email (EmailField) - Email of the Client Partner

\- Client Type (CharField) - Type of the Client (Existing Client/New Client)

\- SF Client Name (CharField) - Name of the client, One of the dimension which we use to Map Actual/Backlog/Target/Plan with Salesforce opportunities data



**financial\_cliententitymapping**

\-----------------------------

Description: Used this to map the Client Tiers



Columns:

\- snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last ingestion before today. The response to the question should be based on latest snapshot date

\- Client (CharField) - Name of the client

\- Partnership level (CharField) - Tier name



#### **Sales Data (Opportunity/Account/User)**

#### **-------------------------------------**



**sales\_opportunity**

**-----------------**

Description: Table which has data of all the deals (opportunities) of the clients.



Columns:

\-------

\- snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last friday data. The response to the question should be based on latest snapshot date

\- Id (CharField) - Unique identifier of each opportunities

\- AccountId (CharField) - Foreign Key Relation with **sales\_account** 

\- Name (CharField) - Name of the deal

\- Description (TextField) - Description or activity happened related to it

\- StageName (CharField) - In what stage the deal is in

\- Probability (FloatField) - Probability of deal, this will change when the stage progresses

\- CloseDate (DataField) - Date which the deal supposed to be closed

\- IsClosed (BooleanField) - Indicates if deal is closed/or not

\- OwnerId (CharField) - Foreign Key relation with **sales\_user**

\- CreatedDate (DateTimeField) - DateTime which the deal was created

\- Annual\_Contracted\_Value\_\_c (FloatField) - ACV of the deal

\- LeadSource (CharField) - Lead Source Info of the deal

\- Company\_Group\_\_c (CharField) -  Company Group Info of the deal

\- Go\_Live\_Date\_\_c (CharField) - Date the deal supposed to start, usually after CloseDate

\- HeadCount\_\_c (CharField) - No. of resources for the deal

\- Resource\_Type\_\_c (CharField) - Type of Resource allocated for the deal

\- Service\_Delivery\_Model\_\_c (CharField) - If the deal is "Agentified Managed Services" or "Non-Agentified Managed Services"

\- LastStageChangeInDays (IntegerField) - No. of days since the stage of the deal changed

\- Revenue\_Type\_\_c (CharField) - If the deal is from New Client/Existing Client

\- LastActivityInDays (IntegerField) - No. of days since an activity happened for the deal.

\- Project\_Duration\_\_c (CharField) - Duration of the project of this deal



**sales\_account**

**-------------**

Description: Details of the account's which has foreign key relation from **sales\_opportunity** via AccountId.



Columns:

\-------

\- snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last friday data. The response to the question should be based on latest snapshot date

\- Id (CharField) - Unique identifier of account

\- Name (CharField) - Name of the account

\- Status\_\_c (CharField) - Status of the account

\- Type (CharField) - Type of account

\- Industry (CharField) - In which Industry the account is in

\- Account\_Type\_\_c (CharField) - If it's New/Existing Client

\- OwnerId (CharField) - Id of the Owner of the account, this has foreign key relation to **sales\_user**

\- Primary\_Account\_Lead\_Source\_\_c (CharField) - Primary Lead Source of the Account

\- Client\_ID\_\_c (CharField) - This is the Id used to map revenue data to sales using MM ID column from **financial\_clientportfoliomapping**



**sales\_user**

**----------**

Description: Details of the user's who has foreign key relation from **sales\_opportunity** and **sales\_account**



Columns:

\-------

\- snapshot\_date (DateField) - Date which we pulled the data from the source, at most will have 2 dates usually. cause we only store day's data. Today and last friday data. The response to the question should be based on latest snapshot date

\- Id (CharField) - Unique identifier of the user

=- Name (CharField) - Name of the User

\- IsActive (BooleanField) - If User is Active/or not

