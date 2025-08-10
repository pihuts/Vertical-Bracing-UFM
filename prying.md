9 –10 DESIGN OF CONNECTING ELEMENTS

BEARING LIMIT STATES
Bearing Strength at Bolt Holes
For available bearing strength at bolt holes, see Part 7.

Steel-on-Steel Bearing Strength (Other Than at Bolt Holes)
Bearing strength for applications other than at bolt holes is determined as given in AISC
Specification Section J7. The fabrication and erection requirements in AISC Specification
Sections M2.6, M2.8 and M4.4 are applicable to connecting elements that transfer load by
contact bearing on steel.

Bearing Strength on Concrete or Masonry
The bearing strength of concrete is determined as given in AISC Specification Section J8. For
bearing on masonry, see Building Code Requirements for Masonry Structures , ACI 530/
ASCE 5/TMS 402 (ACI/ASCE/TMS, 2005a) and Specification for Masonry Structures,
ACI 530.1/ASCE 6/TMS 602 (ACI/ASCE/TMS, 2005b). The fabrication and erection
requirements in AISC Specification Sections M2.8 and M4.1 are applicable to connecting ele-
ments that transfer load by contact bearing on concrete or masonry.

OTHER SPECIFICATION REQUIREMENTS AND DESIGN
CONSIDERATIONS
The following other specification requirements and design considerations apply to the
design of connecting elements:

Prying Action
Prying action is a phenomenon whereby the deformation of a connecting element under a
tensile force increases the tensile force in the bolt above that due to the applied tensile force
alone. Design for prying action includes the selection of bolt diameter and fitting thickness
such that there is sufficient strength in the connecting element and the bolt. The following
discussion of prying action is similar to what has been considered prior to the 13th Edition
Steel Construction Manual , except that the design is based on Fu , which provides better cor-
relation with available test data than previous design methods. For the development of the
prying action equations presented here, see Thornton (1992) and Swanson (2002).
Consider the tee or angle used in a hanger connection as shown in Figure 9-4. The defor-
mation of the connected tee flange or angle leg is assumed to be in double curvature, as
shown in Figure 9-4. The dimension p identifies the tributary length for each bolt shown.
Note that p may be limited by the edge of the plate for the bolt closest to the edge.
The thickness required to eliminate prying action, tmin , is determined as

LRFDASD
t
Tb
pF
min
u
=
Ω 4 ′
t
Tb
pF
min
u
=
4 ′
φ
(9-20a) (9-20b)
φ=0.90 Ω=1.
OTHER SPECIFICATION REQUIREMENTS AND DESIGN CONSIDERATIONS 9 –

where
Fu =specified minimum tensile strength of connecting element, ksi
T =required strength, rut or rat , per bolt, kips

b ′ (9-21)
b =for a tee-type connecting element, the distance from bolt centerline to the face of
the tee stem, in.; for an angle-type connecting element, the distance from bolt cen-
terline to centerline of angle leg, in.
db =bolt diameter, in.
p = tributary length; maximum = 2 b , but ≤ s , unless tests indicate larger lengths can be
used. See Dowswell (2011) and Wheeler et al. (1998).
s = bolt spacing, in.
When the fitting thickness, t , is greater than or equal to tmin , no further check of prying
action is necessary. In this solution, the additional force in the bolt due to prying action, q ,
is essentially zero.
Alternatively, it is usually possible to determine a lesser required thickness by designing
the connecting element and bolted joint for the actual effects of prying action with q greater

Fig. 9-4. Illustration of variables in prying action calculations.
=−⎛
⎝⎜
⎞
⎠⎟
b
db
2
(a) Prying forces in tee (b) Prying forces in angle
φ=0.90 Ω=1.
Table 15-2 can be used to select the preliminary fitting thickness. Subsequently, the thick-
ness required to ensure an acceptable combination of fitting strength and stiffness and bolt
strength, tmin , can be determined as
φ=0.90 Ω=1.
where
δ= (9-24)
=ratio of the net length at bolt line to gross length at the face of the stem or leg of angle
α′ =1.0 if β≥ 1
=the lesser of 1 and if β< 1
d ′=width of the hole along the length of the fitting, in.
β (9-25)
ρ (9-26)
a ′ (9-27)
a =distance from the bolt centerline to the edge of the fitting, in.
B =available tension per bolt, φ rn or rn /Ω, kips
If tmin ≤ t , the preliminary fitting thickness is satisfactory. Otherwise, a fitting with a thicker
flange, or a change in geometry (i.e., b and p ) is required.
Although it is not necessary to do so, if desired, the prying force per bolt, q , can be deter-
mined as
(9-28)
9 –12 DESIGN OF CONNECTING ELEMENTS
=−⎛
⎝⎜
⎞
⎠⎟
1
1
ρ
B
T
=
′
′
b
a
=+⎛
⎝⎜
⎞
⎠⎟
≤+⎛
⎝⎜
⎞
⎠⎟
a
d
b
bbd
2
125
2
.
qB
t
tc
=
⎛
⎝⎜
⎞
⎠⎟
⎡
⎣
⎢
⎢
⎤
⎦
⎥
⎥
δαρ
2
LRFDASD
T
Ft p
b
≤ u^2
Ω 2
T
Ft p
b
≤φ u^2
2
LRFDASD
t
Tb
pF
min
u
=
′
( +′)
Ω 4
1 δα
t
Tb
pF
min
u
=
′
(+′)
4
φδα 1
1 −
d ′
p
1
δ 1
β
−β
⎛
⎝⎜
⎞
⎠⎟
(9-22b)
(9-23b)
(9-22a)
(9-23a)
than zero. To do so, a preliminary fitting thickness, t , can be selected based upon flexural
yielding such that
AISC_PART 9_14th Ed._Nov. 19, 2012 14-11-10 11:13 AM Page 12 (Black plate)

OTHER SPECIFICATION REQUIREMENTS AND DESIGN CONSIDERATIONS 9 –

(9-29)
The parameter αis the ratio of the moment at the face of the tee stem or at the center
of the unconnected angle leg thickness, to the moment at the bolt line. When α=0, the
connection is strong enough to prevent prying action. When α>1 the connection is not
adequate.

tc =flange or angle thickness required to develop the available strength of the bolt, B ,
with no prying action, in.
The total force per bolt including the effects of prying action is then T + q.
Alternatively, when the fitting geometry is known, the available tensile strength per bolt,
B , determined per AISC Specification Sections J3.6 or J3.7, can be multiplied by Q to deter-
mine the available tensile strength including the effects of prying action, Tavail , as follows:

Tavail = BQ (9-31)
When α′ <0, which means that the fitting has sufficient strength and stiffness to develop the
full bolt available tensile strength,
Q = 1 (9-32)

When 0 ≤ α′ ≤1, which means that the fitting has sufficient strength to develop the full bolt
available tensile strength, but insufficient stiffness to prevent prying action,

(9-33)
When α′ >1, which means that the fitting has insufficient strength to develop the full bolt
available tensile strength,

(9-34)
where

(9-35)
= value of αthat either maximizes the bolt available tensile strength for a given thick-
ness or minimizes the thickness required for a given bolt available tensile strength
α
δ
= ⎛ α
⎝⎜
⎞
⎠⎟
−
⎡
⎣
⎢
⎢
⎤
⎦
⎥
⎥
≤≤
1
1
T^2
B
t
t
c where 0 1.
LRFDASD
t
Bb
c
pFu
= ′
t Ω^4
c
Bb
pFu
=
4 ′
φ
Q
t
tc
=⎛
⎝⎜
⎞
⎠⎟
( + ′)
2
1 δα
Q
t
tc
=⎛
⎝⎜
⎞
⎠⎟
( + )
2
1 δ
′=
( + )
⎛
⎝⎜
⎞
⎠⎟
−
⎡
⎣
⎢
⎢
⎤
⎦
⎥
⎥
α
δρ
1
1
1
t^2
t
c
(9-30a) (9-30b)