# Project Reflection

## 1. What I initially thought the project would be

The initial concept was a broad water-quality AI project, potentially including simple risk categories and an interactive interface. At that stage, the technical emphasis was likely to be model training and application construction. Dataset investigation showed that the central challenge was instead defining a scientifically supportable prediction task and evaluation design.

## 2. Why the Safe/Moderate/High Risk idea changed

The selected dataset contains chemistry measurements but no official safety, risk or ecological-status label. Creating Safe, Moderate and High categories would therefore require thresholds from outside the data. Drinking-water standards would not automatically be appropriate for environmental river samples, and arbitrary thresholds would make the model appear more authoritative than its evidence allowed. The classification idea was removed rather than forcing the dataset into the original product concept.

## 3. Why regression became more defensible

Dissolved oxygen is an original continuous measurement with substantial coverage. Predicting it as a number preserves the recorded target instead of creating labels. The objective could also be stated precisely: estimate contemporaneously measured DO from co-measured chemistry at unseen stations. This remains limited, but its target provenance and evaluation criteria are clear.

## 4. What I learned from censoring

A recorded numeric value is not always an exact measurement. A value paired with `<` means that the true concentration was reported below a limit. Treating it as ordinary data or automatically replacing it with half the limit introduces an assumption. Preserving the numeric companion while adding a qualifier indicator made that uncertainty visible to the model and documentation without claiming to recover the unknown concentration.

## 5. What I learned from leakage

Leakage is broader than accidentally including the target as a feature. It can occur when imputation uses the full dataset, when repeated groups appear on both sides of a split, or when final-test performance influences model choices. Preventing leakage required pipelines, group-aware splitting and a strict experiment sequence.

## 6. Why grouped validation changed my understanding of evaluation

Repeated observations from one station are statistically related. A random row split would mainly test performance on a mixture of known locations. Grouping by station changed the generalisation question to performance at unseen monitoring sites. Five GroupKFold splits then showed that results also vary according to which station groups are withheld, making a single split insufficient for model selection.

## 7. Why low-DO error analysis mattered

The final holdout MAE of 0.831 mg/L looked encouraging in isolation. However, the lowest DO decile had MAE 1.812 mg/L and almost 90% of its observations were overpredicted. The overall average hid a structured failure pattern. Error analysis therefore changed the interpretation of the result from a single score to a conditional statement about where the model is and is not reliable.

## 8. Why missing temperature became important

Temperature is an important physical context for dissolved oxygen, but no temperature field exists in the export. Cyclical day-of-year features became highly predictive, yet they cannot replace a direct measurement or establish a mechanism. This limitation helps explain why model interpretation must remain predictive rather than causal and why extreme observations may remain difficult.

## 9. How my view of AI changed

The project demonstrates that applied AI is not defined by adding the most complex model. The strongest work involved checking source credibility, changing an unsupported target, preserving measurement qualifiers, preventing leakage, comparing against a dummy baseline and reporting failure regions. Model metrics became one component of a broader evidence chain rather than the entire result.

## 10. What I would do differently next time

I would define the intended generalisation claim and target provenance before designing an application interface. I would also search earlier for compatible temperature and flow data, pre-register the principal feature comparisons, and plan repeated group validation from the start. If new data became available, I would reserve an external-region test set rather than repeatedly reusing the existing Northern Ireland holdout. I would still begin with simple baselines and delay application development until limitations and prediction wording were stable.

## Development transparency

AI-assisted coding tools were used during implementation and debugging. Project design, dataset selection, modelling decisions, validation strategy, interpretation and documentation were reviewed and directed by the project author.
