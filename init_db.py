import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS businesses')
    cursor.execute('DROP TABLE IF EXISTS services')

    # Adicionando novos campos: short_description, whatsapp, instagram, address
    cursor.execute('''
    CREATE TABLE businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        rating REAL NOT NULL,
        distance TEXT NOT NULL,
        image TEXT NOT NULL,
        featured BOOLEAN NOT NULL,
        about_text TEXT NOT NULL,
        short_description TEXT,
        whatsapp TEXT,
        instagram TEXT,
        address TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price TEXT NOT NULL,
        FOREIGN KEY (business_id) REFERENCES businesses (id)
    )
    ''')

    mock_businesses = [
        (
            'Estúdio Lente Clara', 'Fotografia', 4.9, '1.2 km', 
            'https://images.unsplash.com/photo-1542038784456-1ea8e935640e?q=80&w=600&auto=format&fit=crop', True,
            'Somos um estúdio de fotografia especializado em capturar os melhores momentos da sua vida. Com mais de 10 anos de experiência, oferecemos ensaios fotográficos para casamentos, formaturas, gestantes e corporativos.<br><br>Nossa equipe é formada por profissionais apaixonados por contar histórias através das lentes.',
            'Especialistas em capturar momentos únicos.',
            '(11) 99999-9999',
            '@estudiolenteclara',
            'Rua das Flores, 123 - Centro, São Paulo - SP'
        ),
        (
            'Padaria Artesanal Pão & Prosa', 'Alimentação', 4.8, '0.5 km', 
            'https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=600&auto=format&fit=crop', False,
            'A padaria mais acolhedora do bairro! Pães de fermentação natural feitos todos os dias com muito amor e os melhores ingredientes.',
            'Pães de fermentação natural e cafés especiais.',
            '(11) 98888-8888',
            '@paoeprosa',
            'Av. Paulista, 1000 - Bela Vista, São Paulo - SP'
        ),
        (
            'Oficina do João', 'Mecânica', 4.5, '2.3 km', 
            'https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?q=80&w=600&auto=format&fit=crop', False,
            'Mais de 20 anos cuidando do seu carro como se fosse nosso. Especialistas em mecânica geral, injeção eletrônica, suspensão e freios.',
            'Seu carro em boas mãos, confiança e preço justo.',
            '(11) 97777-7777',
            '@oficinadojoao',
            'Rua Augusta, 500 - Consolação, São Paulo - SP'
        ),
        (
            'Clínica Sorriso Saudável', 'Saúde', 5.0, '1.8 km', 
            'https://images.unsplash.com/photo-1606811841689-23dfddce3e95?q=80&w=600&auto=format&fit=crop', True,
            'Uma clínica odontológica moderna e focada no seu conforto. Nossos especialistas cuidam da sua saúde bucal desde limpezas preventivas até implantes.',
            'Saúde bucal e tratamentos estéticos modernos.',
            '(11) 96666-6666',
            '@sorrisosaudavel',
            'Av. Brigadeiro Faria Lima, 200 - Pinheiros, São Paulo - SP'
        )
    ]

    cursor.executemany('''
    INSERT INTO businesses (name, category, rating, distance, image, featured, about_text, short_description, whatsapp, instagram, address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', mock_businesses)

    mock_services = [
        (1, 'Ensaio Externo (2h)', 'Sessão fotográfica em local externo, entrega de 50 fotos editadas.', 'A partir de R$ 450'),
        (1, 'Cobertura de Casamento', 'Fotografia e Filmagem completa. Making of, cerimônia e festa.', 'Sob consulta'),
        (1, 'Retrato Corporativo', 'Sessão em estúdio para LinkedIn e material de divulgação.', 'A partir de R$ 180'),
        (2, 'Café da Manhã Completo', 'Pão na chapa, café com leite, suco de laranja e fatia de bolo.', 'R$ 35'),
        (2, 'Pão de Fermentação Natural', 'Pão rústico de 500g, casca crocante e miolo macio.', 'R$ 22'),
        (3, 'Revisão Completa', 'Checagem de 40 itens de segurança, troca de óleo e filtros.', 'R$ 380 + peças'),
        (3, 'Alinhamento e Balanceamento', 'Geometria 3D para as 4 rodas do seu veículo.', 'R$ 120'),
        (4, 'Limpeza Dental (Profilaxia)', 'Remoção de tártaro, placa bacteriana e polimento coronário.', 'R$ 250'),
        (4, 'Clareamento a Laser', 'Sessão de clareamento rápido e indolor no consultório.', 'R$ 800')
    ]

    cursor.executemany('''
    INSERT INTO services (business_id, name, description, price)
    VALUES (?, ?, ?, ?)
    ''', mock_services)

    conn.commit()
    conn.close()
    print("Banco de dados atualizado com os campos de perfil avançado!")

if __name__ == '__main__':
    init_db()
