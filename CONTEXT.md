# Context

Glossary of the domain language used in this project. Terms only — no implementation details.

## Parties

**Client**
The company whose credit risk is being assessed (e.g. an electricity trader applying for a loan). Never the lender or the organisation using the tool.
_Avoid:_ customer, borrower (as a code term), bank.

**Peer**
A company in the same sector as the Client, used for comparison.

**Peer group**
The set of Peers a Client is compared against in one Peer Analysis.

## Market structure

**Industry**
A sector the system knows how to research, identified by a short id (e.g. `electricity`, `cereals`). Each Industry has its own list of Sources and its own report outline.

**NACE category**
The EU statistical classification code of an economic activity (e.g. `D35.14 Trade of electricity`). A Client's NACE category determines which Industry its reports draw on.

**Commodity**
A product line through which a Client earns revenue (e.g. wheat, corn, electricity), weighted by its share of the Client's revenue.

**Industry aggregate**
The total of a financial metric across the whole sector for a NACE category, from official statistics. The denominator for a Peer's or Client's market share.

## Research inputs

**Source**
One public origin of market data (a statistics table, an annual report, a price feed) that is collected for an Industry.

**Section**
A part of a report (Market Overview, Price Dynamics, Industry Analysis, Market Players). Each Source declares which Sections it informs.

**Analysis period**
The last two completed calendar years. Reports cover only this period, and Sources are filtered to it.

## Reports

**Market Analysis**
A report on an Industry as a whole: market size, prices, structure and outlook, for a country and Analysis period. Independent of any Client.

**Market Position**
A report on one Client's standing within its market: its share, its Commodity mix, and how it compares to the Market Analysis. Built from the Client's financial statements.

**Peer Analysis**
A report comparing a Client with its Peer group on key financial metrics, including market share against the Industry aggregate.

**Client Report**
The Market Position together with its linked Peer Analysis, as presented and exported for one Client.
