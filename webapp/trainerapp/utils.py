def training_to_file(cui, tui, name, text, start, end, cls, path, synonyms=''):
    # Escape everything
    f = open(path, 'a+')

    cui = cui.replace('"', '\"')
    tui = tui.replace('"', '\"')
    name = name.replace('"', '\"')
    text = text.replace('"', '\"')
    synonyms = synonyms.replace('"', '\"')
    cls = int(cls)

    f.write('"{}","{}","{}","{}",{},{},"{}",{}\n'.format(cui, tui, name, text, start, end,
                                                         synonyms, cls))
    f.close()
