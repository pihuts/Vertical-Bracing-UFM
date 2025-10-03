# Variable Naming Protocol

Quick rules: keep AISC symbols (`F_y`, `L_ev`), reuse names only when the meaning matches, and tag vector outputs with a `results_` prefix. Lengths are in inches, forces in kips, stresses in ksi unless noted.

## Shared payload keys

| Key | Meaning | Provided by |
| --- | --- | --- |
| `designations` | Shape labels (e.g., `W8X10`). | `create_aisc_section_selector` |
| `d`, `bf`, `tf`, `tw`, `Ix`, `Sx`, `Zx` | Section geometry & properties. | `create_aisc_section_selector` |
| `bolt_size` | Nominal bolt diameter. | `generate_bolt_configurations` |
| `bolt_grade_id`, `bolt_grade` | Grade code ↔ label. | `generate_bolt_configurations` |
| `member_a_BHT_id`, `member_a_BHT`, `member_b_BHT_id`, `member_b_BHT` | Hole types. | `generate_bolt_configurations` |
| `N_r`, `S_r`, `N_c`, `S_c` | Bolt layout counts & spacing. | `generate_bolt_configurations` |
| `L_ev`, `L_eh`, `Ga` | Edge distances & gage. | `generate_bolt_configurations` |
| `F_nv`, `F_nt` | Bolt shear / tension strengths. | `generate_bolt_configurations` |

## Variable index

| Symbol | Meaning | Units | Used in | Typical source |
| --- | --- | --- | --- | --- |
| `A_bolt` | Bolt shear area. | in² | `bolt_shear` | Derived from `bolt_size` |
| `E` | Modulus of elasticity. | ksi | `flexural_15th` | Material constants |
| `F_nv` | Bolt shear strength. | ksi | `bolt_shear`, `prying_action` | Bolt config |
| `F_nt` | Bolt tension strength. | ksi | `prying_action` | Bolt config |
| `F_u` | Ultimate strength of plate/member. | ksi | `bolt_bearing`, `block_shear`, `shear_yielding_rupture`, `prying_action`, `flexural_14th`, `flexural_15th` | Section material / input |
| `F_y` | Yield strength of plate/member. | ksi | `block_shear`, `shear_yielding_rupture`, `flexural_14th`, `flexural_15th` | Section material |
| `Ga` / `ga` | Gage / gap. | in | `prying_action` | Bolt config |
| `L` | Lever arm distance. | in | `prying_action` | Connection geometry |
| `L_eh` | Horizontal edge distance. | in | `bolt_bearing`, `block_shear`, `prying_action`, `flexural_14th` | Bolt config |
| `L_ev` | Vertical edge distance. | in | `bolt_bearing`, `block_shear`, `shear_yielding_rupture`, `prying_action`, `flexural_15th` | Bolt config |
| `N_c` | Bolt columns. | count | `bolt_bearing`, `block_shear`, `flexural_14th` | Bolt config |
| `N_r` | Bolt rows. | count | `bolt_bearing`, `block_shear`, `shear_yielding_rupture`, `prying_action`, `flexural_14th`, `flexural_15th` | Bolt config |
| `N_shear_planes` | Bolt shear planes. | count | `bolt_shear` | Connection layout |
| `N_t` | Tension bolts considered. | count | `prying_action` | Connection layout |
| `P_u` | Factored axial demand. | kips | `bolt_bearing`, `block_shear`, `prying_action` | Analysis input |
| `S_c` | Column spacing. | in | `bolt_bearing`, `block_shear`, `flexural_14th` | Bolt config |
| `S_r` | Row spacing. | in | `bolt_bearing`, `block_shear`, `shear_yielding_rupture`, `prying_action`, `flexural_14th`, `flexural_15th` | Bolt config |
| `V_u` | Factored shear demand. | kips | `bolt_bearing`, `block_shear`, `prying_action` | Analysis input |
| `a` | Unbraced length option. | in | `flexural_15th` | Connection geometry |
| `bf` | Flange width (optional). | in | `prying_action` | Section geometry |
| `c` | Bearing coefficient. | – | `bolt_bearing` | Connection input |
| `coped` | Coping flag (0/1/2). | – | `block_shear`, `shear_yielding_rupture` | Connection input |
| `d` | Plate depth / outstanding leg length. | in | `flexural_14th` | Section selector / geometry |
| `d_b` | Bolt diameter for net deduction. | in | `shear_yielding_rupture`, `flexural_14th`, `flexural_15th` | Bolt config |
| `d_bolt` | Bolt diameter. | in | `bolt_bearing`, `prying_action`, `flexural_15th` | Bolt config |
| `d_h` / `dh` | Hole diameter (transverse). | in | `bolt_bearing`, `block_shear` | Bolt config ± tolerance |
| `d_v` / `dv` | Hole diameter (longitudinal). | in | `bolt_bearing`, `block_shear`, `prying_action` | Bolt config ± tolerance |
| `e_override` | Override eccentricity. | in | `flexural_14th` | Analysis input |
| `g_a` | Alt. unbraced length. | in | `flexural_15th` | Connection geometry |
| `k_a` | Outstanding leg setback. | in | `flexural_14th`, `flexural_15th` | Connection detailing |
| `l` | Outstanding leg / eccentricity datum. | in | `flexural_14th` | Connection geometry |
| `member_type` | `'PL'` or `'L'`. | – | `flexural_15th` | Connection definition |
| `n_bolts` | Total bolts. | count | `prying_action` | Connection layout |
| `n_members` | Parallel members. | count | `block_shear`, `shear_yielding_rupture` | Connection input |
| `phi` | Resistance factor. | – | All limit states | Code defaults |
| `prying` | Enable prying amplification. | bool | `prying_action` | Connection option |
| `s_b` / `W` | Alt. unbraced length. | in | `flexural_15th` | Connection geometry |
| `t` | Plate / leg thickness. | in | `bolt_bearing`, `block_shear`, `shear_yielding_rupture`, `prying_action`, `flexural_14th`, `flexural_15th` | Section data |

## Result buffers

| Array | Meaning | Source function |
| --- | --- | --- |
| `results_bearing` | Bearing strength. | `bolt_bearing` |
| `results_block` | Block shear strength. | `block_shear` |
| `results_flexural` | Outstanding leg flexural strength. | `flexural_14th` |
| `results_flexural_15th` | Plate/angle flexural strength. | `flexural_15th` |
| `results_prying` | Prying strength. | `prying_action` |
| `results_shear` | Bolt shear strength. | `bolt_shear` |
| `results_syr` | Shear yielding / rupture strength. | `shear_yielding_rupture` |
