#
# GHGTracker Schema
# these tables are used to setup the database
# and serve as way to validate any data imported into the database
#
# author: Luke Gloege
# Created: 2025-04-28
# Updates:
#   2025-06-23 update emissions breakdown tables

from enum import Enum
from sqlmodel import SQLModel, Column, Field, TIMESTAMP, text, FetchedValue
from typing import Optional
from datetime import datetime

# ============================================================
# Enums
# ============================================================


class ActorType(str, Enum):
    planet = "planet"
    country = "country"
    territory = "territory"
    adm1 = "adm1"
    adm2 = "adm2"
    city = "city"


class AssessmentReport(str, Enum):
    AR1 = "AR1"
    AR2 = "AR2"
    AR3 = "AR3"
    AR4 = "AR4"
    AR5 = "AR5"
    AR6 = "AR6"


class TargetType(str, Enum):
    absolute_reduction = "absolute_reduction"
    target_reduction = "target_reduction"


class AggregationType(str, Enum):
    total = "total"
    total_ex_lulucf = "total_ex_lulucf"


class GasType(str, Enum):
    CO2 = "CO2"
    CH4 = "CH4"
    CH4_fossil = "CH4_fossil"
    CH4_nonfossil = "CH4_nonfossil"
    N2O = "N2O"
    NF3 = "NF3"
    SF6 = "SF6"
    FGASES = "FGASES"
    HFCS = "HFCS"
    PFCS = "PFCS"
    KYOTOGHGS = "KYOTOGHGS"


# ============================================================
# Actor and DataSource
# ============================================================


# track external data sources for actor, emissions, targets, and contexual data
class DataSource(SQLModel, table=True):
    """Data source table

    Attributes:
        id: Unique identifier 
        name: name of the data source
        publisher: publisher of the data source
        published_date: date data set was published
        version: data source version
        url: URL data source was downloaded from
        created_at: date record was created
        updated_at: date record was last updated
    )
    """
    id: str = Field(primary_key=True)
    name: str
    publisher: Optional[str]
    published_date: Optional[datetime]
    version: Optional[str]
    url: Optional[str]
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


# table to track actors (country, subnational, city)
class Actor(SQLModel, table=True):
    """Represents a geographic or political entity.

    Attributes:
        id: Unique identifier for the actor.
        name: Human-readable name of the actor. 

            - For countries, use the
              [ISO 3166-1 alpha-2 code](https://www.iso.org/obp/ui/#iso:pub:PUB500001:en).
            - For subnational regions, such as states and provinces, use the
              [ISO 3166-2 code](https://www.iso.org/obp/ui/#iso:pub:PUB500002:en).
            - For cities, use the
              [UN/LOCODE](https://unece.org/trade/cefact/unlocode-code-list-country).

        is_part_of: ID of the parent actor, if applicable. (e.g. US-NY is_part_of US)
        type: Geographic or political type of the actor.
        datasource_id: ID of the source providing the actor data.
    """
    id: str = Field(primary_key=True)
    name: str
    is_part_of: Optional[str] = Field(default=None, foreign_key="actor.id")
    type: ActorType
    sovereign_code: Optional[str] = Field(default=None, foreign_key="actor.id")
    datasource_id: Optional[str] = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


# ============================================================
#
# Emissions contexual data
# these tables help provide additional details on the emissions
# gas, sector, conversion factors, ...
#
# ============================================================


class GWP(SQLModel, table=True):
    """Global Warming Potential

    Attributes:
        id: Unique identifier for the actor.
        gwp: global warming potential
        time_horizon: time horizon of the GWP (e.g. 100 years)
        gas: gas the GWP is for
        assessment_report: AR1, AR2, AR3, AR4, or AR5
        datasource_id: ID of the source providing the actor data.
    """
    id: str = Field(primary_key=True)
    gwp: float
    time_horizon: int
    gas: GasType
    assessment_report: AssessmentReport
    datasource_id: Optional[str] = Field(default=None, foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class Sector(SQLModel, table=True):
    """Emissions Sector, subsector, and subcategories

    Attributes:
        id: unique id
        code: sector code 
        parent_code: parent code that the sector belongs to
        name: name of the sector, subsector, category, etc.
        taxonomy: sector schema used (e.g. IPCC)
        description: description of the sector field
        datasource_id: data source sector information came from
    """
    id: str = Field(primary_key=True)
    code: str
    parent_code: Optional[str]
    name: str
    taxonomy: Optional[str]  # this should be a Enum
    description: Optional[str]
    datasource_id: Optional[str] = Field(default=None, foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


# to create a sector dag
# useful if a sector belongs to multiple parent categories
class SectorRelation(SQLModel, table=True):
    """Relationship between sectors. For instance parent child relationships.

    Attributes:
        parent_id: str = Field(foreign_key="sector.id", primary_key=True)
        child_id: str = Field(foreign_key="sector.id", primary_key=True)
    """
    parent_id: str = Field(foreign_key="sector.id", primary_key=True)
    child_id: str = Field(foreign_key="sector.id", primary_key=True)


# ============================================================
#
# Emissions and Targets tables
#
# ============================================================


# raw emissions for each gas and sector
class Emissions(SQLModel, table=True):
    """Emissions table

    Attributes:
        id: Unique identifier 
        actor_id: actor responsible for the emissions
        gas: gas
        sector_id: sector emissions are from
        year: year emissions released
        emissions: emissions value
        units: units of emissions (should be same for all)
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    actor_id: str = Field(foreign_key="actor.id")
    gas: GasType
    sector_id: str = Field(foreign_key="sector.id")
    year: int
    emissions: float
    units: str
    datasource_id: Optional[str] = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


# raw emissions in for each gas and sector
# in units of CO2e
# do I even want to include this?
class EmissionsCO2e(SQLModel, table=True):
    """Emissions in CO2-equivalent units

    Attributes:
        id: Unique identifier 
        actor_id: actor responsible for the emissions
        gas: gas
        gwp_id: global warming potential used
        sector_id: sector emissions are from
        year: year emissions released
        emissions: emissions value
        units: units of emissions (should be same for all)
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    actor_id: str = Field(foreign_key="actor.id")
    sector_id: str = Field(foreign_key="sector.id")
    gas: GasType
    gwp_id: Optional[str] = Field(foreign_key="gwp.id")
    assessment_report: AssessmentReport
    year: int
    emissions: float
    units: str
    datasource_id: Optional[str] = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class EmissionsTotalSector(SQLModel, table=True):
    """Emissions aggregated across sector

    Attributes:
        id: Unique identifier 
        actor_id: actor responsible for the emissions
        sector_id: sector emissions are from
        year: year emissions released
        emissions: emissions value
        assessment_report: assement report used to calculate GWP
        gases_included: string with gases included in the sector
        units: units of emissions (should be same for all)
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    actor_id: str = Field(foreign_key="actor.id")
    sector_id: str = Field(foreign_key="sector.id")
    year: int
    emissions: float
    assessment_report: AssessmentReport
    gases_included: Optional[str]
    units: str
    datasource_id: Optional[str] = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class EmissionsTotalCO2e(SQLModel, table=True):
    """Total Emissions in CO2-equivalent units

    Attributes:
        id: Unique identifier 
        actor_id: actor responsible for the emissions
        year: year emissions released
        emissions: emissions value
        aggregation_type: either  "total" or "total_ex_lulucf" (which excluded LULUCF sector)
        assessment_report: assement report used to calculate GWP
        gases_included: string with gases included in the sector
        units: units of emissions (should be same for all)
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    actor_id: str = Field(foreign_key="actor.id")
    year: int
    emissions: float
    aggregation_type: AggregationType
    units: str
    assessment_report: AssessmentReport
    gases_included: Optional[str]
    datasource_id: Optional[str] = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class Targets(SQLModel, table=True):
    """Emissions Targets Table

    Attributes:
        id: Unique identifier 
        actor_id: actor with the target
        target_type: either "absolute_reduction" or "target_reduction" (more can be added)
        target_value: reduction value
        target_year: year target is to be achieved
        baseline_year: year whose emissions are used as a baseline for the target_value
        url: URL for the target
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    actor_id: str = Field(foreign_key="actor.id")
    target_type: TargetType
    target_value: float
    baseline_year: int
    target_year: int
    url: Optional[str]
    datasource_id: str = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


# ============================================================
#
# Contextual data
# these tables provide additional information on the actors
# and were intially intended for use with the Kaya identity
#
# ============================================================


class GDP(SQLModel, table=True):
    """Gross Domestic Product

    Attributes:
        id: Unique identifier 
        year: year of GDP
        actor_id: actor with the GDP
        gdp: GDP value in dollars
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    year: int
    actor_id: str = Field(foreign_key="actor.id")
    gdp: float
    datasource_id: str = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class Population(SQLModel, table=True):
    """Gross Domestic Product

    Attributes:
        id: Unique identifier 
        year: year of population
        actor_id: actor with the population
        population: population of actor in given year
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    year: int
    actor_id: str = Field(foreign_key="actor.id")
    population: int
    datasource_id: str = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )


class EnergyConsumption(SQLModel, table=True):
    """Energy Consumption

    Attributes:
        id: Unique identifier 
        year: year of GDP
        actor_id: actor with the GDP
        consumption: energy consumption data
        units: units of energy consumption (e.g. TJ, GwH, ...)
        fuel_type: e.g. coal, solar, oil
        energy_source: either "fossil" or "renewable"
        datasource_id: data source where data came from
        created_at: date record was created
        updated_at: date record was last updated
    """
    id: str = Field(primary_key=True)
    year: int
    actor_id: str = Field(foreign_key="actor.id")
    consumption: float
    units: str  # e.g., "TJ", "Mtoe", "GWh"
    fuel_type: str  # e.g., "coal", "solar", "oil" maybe enum?
    energy_source: str  # e.g., "fossil", "renewable" maybe this should be enum?
    datasource_id: str = Field(foreign_key="datasource.id")
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            server_onupdate=FetchedValue(),
        )
    )
