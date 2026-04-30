# Example EEG/ERP Methods Text with Better Reporting

Forty-eight participants were recruited; after excluding four participants due to excessive EEG artifacts, forty-four participants entered the final ERP analysis. EEG was recorded from 64 Ag/AgCl electrodes mounted according to the extended 10-20 system using a Brain Products actiCAP system. The online reference was FCz and the ground was AFz. Electrode impedances were kept below 10 kΩ. Data were sampled at 500 Hz.

Offline preprocessing was conducted in MNE-Python 1.7. The continuous EEG was re-referenced to the average of the left and right mastoids. Data were filtered with a zero-phase FIR band-pass filter from 0.1 to 30 Hz and a 50 Hz notch filter. Epochs were extracted from -200 to 1000 ms relative to stimulus onset and baseline-corrected using -200 to 0 ms. Bad channels were identified by visual inspection and interpolated using spherical splines. ICA was fitted on the 1 Hz high-pass filtered copy of the continuous data; ocular components were identified using correlation with VEOG/HEOG channels and ICLabel probabilities and then removed from the 0.1 Hz filtered data.

Trials exceeding ±100 µV at any EEG channel were rejected. The final number of accepted trials was reported per condition: congruent M = 72, SD = 8; incongruent M = 70, SD = 9.

The N400 was quantified as mean amplitude from 300 to 500 ms at a centro-parietal ROI (Cz, CPz, Pz), selected a priori based on previous N400 studies. The LPP was quantified from 500 to 800 ms at Pz, CPz, and Cz. Repeated-measures ANOVAs tested Condition effects separately for the pre-registered N400 and LPP windows. Holm correction was applied across the two primary ERP tests. Partial eta squared and 95% confidence intervals are reported for all primary effects.
