# API Specification: Mayon Radar Watch

| Version | Status | Last updated | Based on |
| --- | --- | --- | --- |
| 0.1 | Draft | 2026-10-31 | 01 v0.1 (Draft), 02 v0.1 (Draft), 04 v0.1 (Draft), 05 v0.1 (Draft) |

This system has no backend (04, ADR-001). Its "API" is the set of static files the pipeline publishes and the web app reads. This document is the contract between the two halves, so the pipeline and the web app can be built in parallel and checked automatically (04 §3, `contract_check`). Outbound calls from the pipeline to ASF and Earthdata are third-party services, described in 04 §6.

## 1. Conventions

| Item | Rule |
| --- | --- |
| Base URL | `https://<github-user>.github.io/<repository>` [TBD]; the app requests paths relative to its own page, so the same paths work on localhost |
| Auth | None: every file is public and read-only (PRD §4) |
| Methods | `GET` only |
| Format | JSON (UTF-8) with the envelope below; GeoJSON (RFC 7946) `FeatureCollection` with `generated_at` and `schema_version` members; PNG or WebP images; little-endian binary grids |
| Field naming | `snake_case`, exactly the column names in 05 |
| Dates and times | ISO 8601: `date-time` in UTC (e.g. `2026-10-19T21:13:19Z`), `date` as `YYYY-MM-DD` |
| Pagination | Not applicable: one site gains about 30 pairs per year per track, so lists stay small |
| IDs | Strings, in the patterns defined in 05 |
| Caching | The host's default caching applies (verify); a new publish changes `generated_at` |

**Success response shape (JSON files)**

```json
{
  "data": {},
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

All examples below use the real track 111 granules from Oct 7 and Oct 19, 2026 (progress notes). Every computed or not-yet-decided number in them (areas, thresholds, zoom levels, image sizes, colors) is illustrative only.

## 2. Errors

A static host doesn't return JSON errors. A missing file returns HTTP 404 with the host's HTML page. The web app's `data.js` turns every failure into one internal error object, and the screens show the messages from 01 and 03:

**Error response shape** (internal to the web app, not sent over HTTP)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Couldn't load Mayon Volcano, Albay. Try again.",
    "details": [
      { "field": "url", "issue": "data/sites/mayon/pairs.json returned 404" }
    ]
  }
}
```

| HTTP status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | The file doesn't exist on the host |
| 5xx | `SERVER_ERROR` | The host itself fails |
| — (no response) | `NETWORK_ERROR` | Offline, DNS failure, or no response within [TBD] s |
| 200 | `INVALID_DATA` | The file arrives but can't be parsed, has an unknown `schema_version`, or misses a required field from 05 |

400, 401, 403, 409 and 429 are not applicable: there is no input, no login and no write access.

## 3. Endpoint Summary

| API-ID | Method | Path | Description | Roles | FR / US | MVP |
| --- | --- | --- | --- | --- | --- | --- |
| API-001 | GET | `/data/sites.json` | Published sites | Visitor, Maintainer | FR-001, FR-004, FR-006, FR-041, FR-042, US-001, US-002, US-014 | Yes |
| API-002 | GET | `/data/sources.json` | Context data sources | Visitor, Maintainer | FR-040, FR-058, US-013, US-023 | Yes |
| API-003 | GET | `/data/sites/{site_id}/towns.geojson` | Town borders and names | Visitor, Maintainer | FR-002, FR-007, FR-008, FR-009, FR-010, US-001, US-003, US-004 | Yes |
| API-004 | GET | `/data/sites/{site_id}/land.geojson` | Land polygon for the coastline | Visitor, Maintainer | FR-003, FR-005, FR-011, US-001, US-004 | Yes |
| API-005 | GET | `/data/sites/{site_id}/channels.geojson` | Named channels and their towns | Visitor, Maintainer | FR-056, FR-057, US-023 | Yes |
| API-006 | GET | `/data/sites/{site_id}/events.json` | Events for timeline markers | Visitor, Maintainer | FR-016, US-005 | Yes |
| API-007 | GET | `/data/sites/{site_id}/pairs.json` | Published pairs, oldest first | Visitor, Maintainer | FR-013, FR-015, FR-017, FR-018, FR-059, US-005, US-006 | Yes |
| API-008 | GET | `/data/sites/{site_id}/pairs/{pair_id}/pair.json` | One pair with its passes and layers | Visitor, Maintainer | FR-014, FR-019, FR-020, FR-025, FR-026, FR-039, US-005, US-007, US-008, US-013 | Yes |
| API-009 | GET | `/data/sites/{site_id}/pairs/{pair_id}/{image_path}` | Layer image | Visitor, Maintainer | FR-019, FR-025, US-007, US-008 | Yes |
| API-010 | GET | `/data/sites/{site_id}/pairs/{pair_id}/{grid_path}` | Layer value grid | Visitor, Maintainer | FR-010, FR-011, FR-057, US-004, US-023 | Yes |
| API-011 | GET | `/data/sites/{site_id}/pairs/{pair_id}/validation.json` | Validation of one pair | Visitor, Maintainer | FR-048, US-017 | Yes |

## 4. Endpoint Details

### API-001: `GET /data/sites.json`

**Purpose:** List published sites with their map settings.
**Roles:** Visitor, Maintainer
**Supports:** FR-001, FR-004, FR-006, FR-041, FR-042, US-001, US-002, US-014

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| — | — | — | — | None |

**Request body**

None (`GET`).

**Success response:** `200 OK`

```json
{
  "data": [
    {
      "id": "mayon",
      "name": "Mayon Volcano, Albay",
      "country": "Philippines",
      "status": "published",
      "time_zone": "Asia/Manila",
      "center_lat": 13.2572,
      "center_lon": 123.6856,
      "bounds_west": 123.56,
      "bounds_south": 13.14,
      "bounds_east": 123.81,
      "bounds_north": 13.38,
      "default_zoom": 12,
      "min_zoom": 10,
      "max_zoom": 16,
      "summit_lat": 13.2572,
      "summit_lon": 123.6856,
      "danger_zone_radius_km": 6,
      "danger_zone_label": "Permanent Danger Zone (6 km)",
      "change_types": ["new_material"],
      "created_at": "2026-11-04T09:00:00Z",
      "updated_at": "2026-11-04T09:00:00Z"
    }
  ],
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Nothing has been published yet; Suggestion: "Couldn't load the site list. Try again." (03 SCR-08) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | A site breaks a 05 constraint, e.g. `bounds_west` ≥ `bounds_east` |

### API-002: `GET /data/sources.json`

**Purpose:** List context data sources for the Data sources panel.
**Roles:** Visitor, Maintainer
**Supports:** FR-040, FR-058, US-013, US-023

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| — | — | — | — | None |

**Request body**

None (`GET`).

**Success response:** `200 OK`

```json
{
  "data": [
    {
      "id": "ph_admin_boundaries",
      "name": "Philippine municipal and city boundaries",
      "provider": "NAMRIA and PSA via OCHA COD-AB, packaged by faeldon/philippines-json-maps",
      "used_for": "boundaries",
      "url": "https://github.com/faeldon/philippines-json-maps",
      "license": "CC BY-IGO",
      "retrieved_on": "2026-10-30",
      "created_at": "2026-11-04T09:00:00Z",
      "updated_at": "2026-11-04T09:00:00Z"
    }
  ],
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | File missing |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | A source lacks `license` or `url` |

### API-003: `GET /data/sites/{site_id}/towns.geojson`

**Purpose:** Town borders and names for drawing, search and readouts.
**Roles:** Visitor, Maintainer
**Supports:** FR-002, FR-007, FR-008, FR-009, FR-010, US-001, US-003, US-004

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK` (geometry shortened to one small ring for the example)

```json
{
  "type": "FeatureCollection",
  "generated_at": "2026-11-04T09:00:00Z",
  "schema_version": "1.0",
  "features": [
    {
      "type": "Feature",
      "id": "mayon_tabaco_city",
      "properties": {
        "id": "mayon_tabaco_city",
        "site_id": "mayon",
        "name": "Tabaco City",
        "kind": "city",
        "label_lat": 13.3592,
        "label_lon": 123.7338,
        "source_code": null,
        "source_id": "ph_admin_boundaries"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[123.70, 13.33], [123.76, 13.33], [123.76, 13.38], [123.70, 13.38], [123.70, 13.33]]]
      }
    }
  ]
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Unknown `site_id` or file missing |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | Invalid geometry or missing `name` |

### API-004: `GET /data/sites/{site_id}/land.geojson`

**Purpose:** Land polygon for the coastline and for the "sea" no-data reason.
**Roles:** Visitor, Maintainer
**Supports:** FR-003, FR-005, FR-011, US-001, US-004

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK` (geometry shortened)

```json
{
  "type": "FeatureCollection",
  "generated_at": "2026-11-04T09:00:00Z",
  "schema_version": "1.0",
  "features": [
    {
      "type": "Feature",
      "id": "mayon_land",
      "properties": {
        "id": "mayon_land",
        "site_id": "mayon",
        "source_id": "ph_admin_boundaries"
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[123.56, 13.14], [123.81, 13.14], [123.81, 13.38], [123.56, 13.38], [123.56, 13.14]]]]
      }
    }
  ]
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Unknown `site_id` or file missing |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | Invalid geometry |

### API-005: `GET /data/sites/{site_id}/channels.geojson`

**Purpose:** Named channels with their towns and sources.
**Roles:** Visitor, Maintainer
**Supports:** FR-056, FR-057, US-023

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK` (line shortened; the line source is still [TBD])

```json
{
  "type": "FeatureCollection",
  "generated_at": "2026-11-04T09:00:00Z",
  "schema_version": "1.0",
  "features": [
    {
      "type": "Feature",
      "id": "mayon_miisi",
      "properties": {
        "id": "mayon_miisi",
        "site_id": "mayon",
        "name": "Mi-isi",
        "alt_names": ["Miisi"],
        "town_ids": ["mayon_daraga"],
        "name_source": "PHIVOLCS Mayon Volcano Bulletin",
        "name_source_url": null,
        "line_source_id": "channel_lines"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [[123.680, 13.250], [123.700, 13.200], [123.710, 13.160]]
      }
    }
  ]
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Unknown `site_id` or file missing; Suggestion: the channel layer is hidden and the legend says "Channels unavailable" (03 §5) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | A `town_ids` item doesn't exist in `towns.geojson` |

### API-006: `GET /data/sites/{site_id}/events.json`

**Purpose:** Events for timeline markers.
**Roles:** Visitor, Maintainer
**Supports:** FR-016, US-005

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK`

```json
{
  "data": [
    {
      "id": "mayon_20261030_eruption",
      "site_id": "mayon",
      "name": "Moderately explosive eruption",
      "event_date": "2026-10-30",
      "description": "PHIVOLCS raised Mayon to Alert Level 3 after an eruption at 11:53 AM.",
      "source_name": "Manila Bulletin, citing PHIVOLCS",
      "source_url": "https://mb.com.ph/2026/10/30/mayon-volcano-alert-status-raised-to-level-3",
      "created_at": "2026-11-04T09:00:00Z",
      "updated_at": "2026-11-04T09:00:00Z"
    }
  ],
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | File missing; Suggestion: the timeline shows no event markers (03 §5) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | `event_date` isn't a valid date |

### API-007: `GET /data/sites/{site_id}/pairs.json`

**Purpose:** Every published pair of a site, oldest first by `after_acquired_start`.
**Roles:** Visitor, Maintainer
**Supports:** FR-013, FR-015, FR-017, FR-018, FR-059, US-005, US-006

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK`. An empty `data` array means no published pairs (FR-018).

```json
{
  "data": [
    {
      "id": "mayon_A111F008_20261007_20261019",
      "site_id": "mayon",
      "status": "published",
      "track": 111,
      "frame": 8,
      "orbit_direction": "ascending",
      "before_pass_id": "A111F008_20261007T211319",
      "after_pass_id": "A111F008_20261019T211319",
      "before_acquired_start": "2026-10-07T21:13:19Z",
      "after_acquired_start": "2026-10-19T21:13:19Z",
      "previous_pair_id": "mayon_A111F008_20260925_20261007",
      "gunw_granule_id": "NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001",
      "gunw_vertex_url": "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList=NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001",
      "coherence_used": true,
      "brightness_threshold_db": 3.0,
      "coherence_loss_threshold": 0.3,
      "high_confidence_area_km2": 0.05,
      "low_confidence_area_km2": 0.21,
      "new_material_area_km2": 0.26,
      "pipeline_version": "0.1.0",
      "error_message": null,
      "published_at": "2026-11-04T09:00:00Z",
      "created_at": "2026-11-04T08:40:00Z",
      "updated_at": "2026-11-04T09:00:00Z"
    }
  ],
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Unknown `site_id` or file missing; the screen shows the site error with Retry (FR-042) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | A pair has a `status` other than `published` (FR-059), or `new_material_area_km2` ≠ high + low |

### API-008: `GET /data/sites/{site_id}/pairs/{pair_id}/pair.json`

**Purpose:** One pair with its two passes and all its layers.
**Roles:** Visitor, Maintainer
**Supports:** FR-014, FR-019, FR-020, FR-025, FR-026, FR-039, US-005, US-007, US-008, US-013

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |
| `pair_id` | path | string | Yes | `pairs.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK` (one pass and one layer shown in full; the real file has 2 passes and 5 layers)

```json
{
  "data": {
    "id": "mayon_A111F008_20261007_20261019",
    "site_id": "mayon",
    "status": "published",
    "track": 111,
    "frame": 8,
    "orbit_direction": "ascending",
    "before_pass_id": "A111F008_20261007T211319",
    "after_pass_id": "A111F008_20261019T211319",
    "before_acquired_start": "2026-10-07T21:13:19Z",
    "after_acquired_start": "2026-10-19T21:13:19Z",
    "previous_pair_id": "mayon_A111F008_20260925_20261007",
    "gunw_granule_id": "NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001",
    "gunw_vertex_url": "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList=NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001",
    "coherence_used": true,
    "brightness_threshold_db": 3.0,
    "coherence_loss_threshold": 0.3,
    "high_confidence_area_km2": 0.05,
    "low_confidence_area_km2": 0.21,
    "new_material_area_km2": 0.26,
    "pipeline_version": "0.1.0",
    "error_message": null,
    "published_at": "2026-11-04T09:00:00Z",
    "created_at": "2026-11-04T08:40:00Z",
    "updated_at": "2026-11-04T09:00:00Z",
    "passes": [
      {
        "id": "A111F008_20261007T211319",
        "site_id": "mayon",
        "mission": "NISAR",
        "product_type": "GCOV",
        "granule_id": "NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001",
        "track": 111,
        "frame": 8,
        "orbit_direction": "ascending",
        "cycle": 32,
        "acquired_start": "2026-10-07T21:13:19Z",
        "acquired_end": "2026-10-07T21:13:54Z",
        "polarizations": ["HHHH", "HVHV"],
        "pixel_spacing_m": 10,
        "maturity": "PROVISIONAL",
        "vertex_url": "https://search.asf.alaska.edu/#/?dataset=NISAR&searchType=List%20Search&searchList=NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001",
        "created_at": "2026-11-04T08:40:00Z",
        "updated_at": "2026-11-04T08:40:00Z"
      }
    ],
    "layers": [
      {
        "id": "mayon_A111F008_20261007_20261019_new_material",
        "pair_id": "mayon_A111F008_20261007_20261019",
        "kind": "new_material",
        "title": "New material",
        "units": "class",
        "image_path": "new_material.png",
        "image_format": "png",
        "bounds_west": 123.56,
        "bounds_south": 13.14,
        "bounds_east": 123.81,
        "bounds_north": 13.38,
        "image_width": 1350,
        "image_height": 1300,
        "grid_path": "new_material.bin",
        "grid_dtype": "uint8",
        "grid_scale": 1,
        "grid_nodata": null,
        "no_data_codes": {
          "253": "masked_by_product",
          "254": "sea",
          "255": "outside_coverage"
        },
        "grid_width": 1350,
        "grid_height": 1300,
        "color_scale_min": null,
        "color_scale_max": null,
        "legend": [
          { "value": 1, "label": "Possible new material (one signal)", "color": "#E69F00", "confidence": "low" },
          { "value": 2, "label": "New material (both signals)", "color": "#D55E00", "confidence": "high" }
        ],
        "source_granule_ids": [
          "NISAR_L2_PR_GCOV_032_111_A_008_4005_DHDH_A_20261007T211319_20261007T211354_P05023_N_F_J_001",
          "NISAR_L2_PR_GCOV_033_111_A_008_4005_DHDH_A_20261019T211319_20261019T211354_P05023_N_F_J_001",
          "NISAR_L2_PR_GUNW_032_111_A_008_033_4000_SH_20261007T211319_20261007T211354_20261019T211319_20261019T211354_P05023_N_F_J_001"
        ],
        "created_at": "2026-11-04T08:40:00Z",
        "updated_at": "2026-11-04T08:40:00Z"
      }
    ]
  },
  "meta": {
    "generated_at": "2026-11-04T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Unknown `pair_id`; Suggestion message "Couldn't load this pass. Try again." (03 §5) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | Missing `passes` or `layers`; a layer without `legend` or `source_granule_ids` (NFR-008) |

### API-009: `GET /data/sites/{site_id}/pairs/{pair_id}/{image_path}`

**Purpose:** One layer image, placed on the map at the layer's bounds.
**Roles:** Visitor, Maintainer
**Supports:** FR-019, FR-025, US-007, US-008

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |
| `pair_id` | path | string | Yes | `pairs.id` |
| `image_path` | path | string | Yes | `layers.image_path`, e.g. `before_db.png` |

**Request body**

None (`GET`).

**Success response:** `200 OK`, `Content-Type: image/png` or `image/webp`. Transparent outside the data. Pixel (0, 0) is the north-west corner of the layer's bounds.

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Image missing; for `before_db` or `after_db`, the Compare view shows "Before/after images not available for this pair" (FR-020) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | Image size differs from `image_width` × `image_height` |

### API-010: `GET /data/sites/{site_id}/pairs/{pair_id}/{grid_path}`

**Purpose:** One layer's value grid, read in the browser for readouts.
**Roles:** Visitor, Maintainer
**Supports:** FR-010, FR-011, FR-057, US-004, US-023

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |
| `pair_id` | path | string | Yes | `pairs.id` |
| `grid_path` | path | string | Yes | `layers.grid_path`, e.g. `new_material.bin` |

**Request body**

None (`GET`).

**Success response:** `200 OK`, raw bytes. Size = `grid_width` × `grid_height` × bytes per `grid_dtype` (1 for `uint8` and `int8`, 2 for `int16`). Little-endian, row by row from north to south, each row from west to east. For the `new_material` grid, values are `new_material_class` (0, 1, 2) or a `no_data_codes` key (253, 254, 255).

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Grid missing; the readout says "Couldn't load radar values. Try again." (Suggestion, 03 SCR-02) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | Byte count doesn't match the expected size |

### API-011: `GET /data/sites/{site_id}/pairs/{pair_id}/validation.json`

**Purpose:** Validation of one pair against an independent source.
**Roles:** Visitor, Maintainer
**Supports:** FR-048, US-017

**Path and query parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `site_id` | path | string | Yes | `sites.id` |
| `pair_id` | path | string | Yes | `pairs.id` |

**Request body**

None (`GET`).

**Success response:** `200 OK` (illustrative values; no real check exists yet)

```json
{
  "data": {
    "id": "val_mayon_A111F008_20261019_20261031",
    "pair_id": "mayon_A111F008_20261019_20261031",
    "source_name": "PHIVOLCS Mayon Volcano Bulletin",
    "source_url": "https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin",
    "source_date": "2026-11-01",
    "method": "Each gully named in the bulletin was compared with the new-material layer inside a 500 m buffer of its channel line.",
    "created_at": "2026-11-05T09:00:00Z",
    "updated_at": "2026-11-05T09:00:00Z",
    "items": [
      {
        "id": "item_01",
        "validation_id": "val_mayon_A111F008_20261019_20261031",
        "place_name": "Mi-isi Gully",
        "channel_id": "mayon_miisi",
        "reported_in_source": true,
        "detected": "yes",
        "note": null,
        "created_at": "2026-11-05T09:00:00Z",
        "updated_at": "2026-11-05T09:00:00Z"
      }
    ]
  },
  "meta": {
    "generated_at": "2026-11-05T09:00:00Z",
    "schema_version": "1.0"
  }
}
```

**Errors**

| Status | Code | When |
| --- | --- | --- |
| 404 | `NOT_FOUND` | No validation for this pair; not an error for visitors: the panel shows "Not yet checked against an independent source" (FR-048) |
| — | `NETWORK_ERROR` | No connection |
| 200 | `INVALID_DATA` | `detected` isn't a `detection_result` value |

## 5. Rate Limiting and Security

| Endpoint or group | Limit | Reason |
| --- | --- | --- |
| All endpoints | None set by this system; the host's own limits apply (verify) | Static public files; NFR-006 |
| All endpoints | HTTPS only | NFR-002 |
| All endpoints | Read-only `GET`; nothing a visitor sends is stored | NFR-007 |

## 6. Assumptions

- The app and its data are served from the same host, so no cross-origin setup is needed.
- A missing `validation.json` is normal and means "not yet checked".
- `pairs.json` holds only published pairs, so the web app never filters by status itself.

## 7. Open Questions

| # | Question | Affects |
| --- | --- | --- |
| 1 | What are the GitHub username and repository name for the base URL? | §1 |
| 2 | How long should the app wait before treating a request as a network error? | §2 |
| 3 | Is the ASF Vertex list-search link format used in the examples correct? (verify) | API-007, API-008 |
| 4 | What channel buffer should validation use? (500 m in the example is illustrative; same question as the channel distance in 01 Open Question 3) | API-011 |

## 8. Conflicts with Earlier Documents

None.

## 9. Revision History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-10-31 | First draft |
