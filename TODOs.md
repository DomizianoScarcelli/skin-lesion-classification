-   [x] See the results with the segmentation but without stretching the image, so first apply the bounding box and then the segmentation (or vice versa).
-   [x] Try to remove the small factor for the division by 0 for the std in the normalization and see if the results are better.
-   [ ] Test with 700 x 700 bbox segmentation, applying zoom out to the zi and to zs (zs_bbox is the only one that is already 700 x 700), and compare the results with the previous point, where you used the 450 x 600 zs_bbox.
-   [ ] Fine tune SAM
-   [ ] Get the segmentation mask dynamically with SAM
-   [x] Handle the normalization before or after the image loading with the different dataloaders
-   [ ] Python CLI to train different models with different techniques via a shell script
-   [ ] Sistema normalizzazione
-   [ ] Controlla labels
-   [ ] Fixa test e testa la robba del tutto training