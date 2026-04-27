# dead-exception

Demonstrates the dead-class failure mode observed in the pilot: a CREQ advertises a five-class exception hierarchy, but the source only actually raises two of them. `exception_raise_sites_exist` fails with evidence naming all three classes missing raise sites. Remaining axes pass — named-symbol existence still holds because the classes are defined (just never raised), and the CREQ explicitly enumerates each case so the branch-count axis scores 3.
