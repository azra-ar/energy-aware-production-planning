# Data sources and quality

## Primary source

- Record: https://zenodo.org/records/4106746
- DOI: 10.5281/zenodo.4106746
- Source filename: Input_JSON_Schedule_Optimization.json
- Creators: Bruno Mota, Luis Gomes, Pedro Faria, Carlos Ramos and Zita Vale
- Version: 0.1
- Publication date: 2020-11-05
- Licence identifier in the retained source metadata: mit-license
- SHA256 of the included source file: `5cecb2eb95437d6b789726f302860cefb446731af9eadba2a8379af5644ed169`

The source JSON bytes are copied without editing. A copy of the retrieved Zenodo record metadata is retained alongside it. The related paper is https://doi.org/10.3390/en14020462.

## Units and model use

The paper describes energy per time interval and a five-minute case-study resolution. Source profile values are used as Wh per interval and source Socket Energy prices as EUR/Wh. The main experiments compare complete daily price profiles known in advance. Prices and manufacturing profiles come from the published case-study inputs; assumed daily demand allocation and setup durations are labelled modelling choices.

## Identified gaps

`Harden[1] TM2` appears in the task and mode definitions but is not assigned to any machine. It is recorded as an excluded unassigned mode, not guessed or assigned to a machine. It is not needed by the three selected products.

Only one source request has an explicit deadline. The selected daily studies impose their own common 23:00 completion limit; they do not claim observed individual customer due dates.

The JSON Order constraint uses first_task and second_task fields for Harden processes, while the paper's prose describes a precedence relationship whose field direction requires clarification before extending the model. The selected system excludes those processes. Product task-list order alone is not treated as confirmed precedence.

The source does not establish measured initial/setup times, setup energy, idle energy or all practical handling restrictions. Values used for these are scenario assumptions. The code checks that each selected product has a single required task, with one run, and that its chosen mode is assigned to MAQ120.
