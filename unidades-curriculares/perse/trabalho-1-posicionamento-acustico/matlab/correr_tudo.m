% Corre as 4 demos e guarda as figuras em PNG (pasta figuras/)
if ~exist('figuras', 'dir'), mkdir('figuras'); end
demos = {'demo1_velocidade_som', 'demo2_lbl', 'demo3_usbl', 'demo4_comparacao', 'demo5_orcamento_enlace', 'demo6_kalman_lbl_dvl'};
for k = 1:numel(demos)
    fprintf('\n===== %s =====\n', demos{k});
    run(demos{k});
    figs = findall(0, 'type', 'figure');
    for f = figs'
        nome = strrep(get(f, 'Name'), ' ', '');
        set(f, 'Position', [100 100 1200 520]);
        print(f, fullfile('figuras', [nome '.png']), '-dpng', '-r110');
    end
end
